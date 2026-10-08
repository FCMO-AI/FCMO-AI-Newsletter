#!/usr/bin/env python3
"""Measure the real translation backlog, field by field.

Publication stays fail-open to canonical English, but localization health is its
own signal. A (story, locale) pair counts as translated only when every prose
field of the English record has a native counterpart (see
``validate_localizations.pair_status``); a headline-only delta is backlog.

``--all-corpus`` (the health signal)
    Every live story of ``--corpus``. A pair that is incomplete for longer than
    ``--grace-hours`` after the story was first published is backlog. The first
    stdout line is one of::

        BACKLOG es-419=<n> zh-Hans=<n>   exit 1  (some pair is overdue)
        GRACE es-419=<n> zh-Hans=<n>     exit 0  (incomplete pairs, all within grace)
        HEALTHY es-419=0 zh-Hans=0       exit 0

    and the second line is a JSON payload (``--out`` also writes it to a file).
    Exit 2 means the input could not be read.

default (the legacy recent-story SLO)
    Only material stories published within ``--fresh-window-hours``; same
    field-level completeness; prints one JSON object and exits 1 when a recent
    material story is overdue.

Time comes from ``--now``, else ``FCMO_NOW``, else the clock.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from tools.validate_localizations import (
        LOCALES,
        effective_overlays_details,
        load_locale_details,
        is_complete,
        load_corpus_canonical,
        pair_status,
        resolve_now,
        utc_text,
    )
except ImportError:  # direct script execution from tools/
    from validate_localizations import (
        LOCALES,
        effective_overlays_details,
        load_locale_details,
        is_complete,
        load_corpus_canonical,
        pair_status,
        resolve_now,
        utc_text,
    )


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def first_published(corpus: Path, canonical: dict[str, dict[str, Any]]) -> dict[str, datetime]:
    """When each story first went public.

    The first-publication ledger wins; otherwise the record's ``recorded_at``;
    otherwise the airlock time. A story without any of them is treated as
    published long ago (never as brand new), so it cannot hide in the grace
    window.
    """
    ledger: dict[str, Any] = {}
    path = corpus / "first-published.json"
    if path.is_file():
        ledger = json.loads(path.read_text(encoding="utf-8")).get("entries") or {}
    airlock = None
    if (corpus / "airlock.json").is_file():
        raw = json.loads((corpus / "airlock.json").read_text(encoding="utf-8")).get("generated_at")
        airlock = parse_time(raw) if raw else None
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    out: dict[str, datetime] = {}
    for rid, row in canonical.items():
        entry = ledger.get(rid) if isinstance(ledger, dict) else None
        raw = (entry or {}).get("first_published_at") or row.get("recorded_at")
        try:
            out[rid] = parse_time(raw) if raw else (airlock or epoch)
        except ValueError:
            out[rid] = airlock or epoch
    return out


def corpus_health(corpus: Path, i18n_dir: Path | None, now: datetime, grace_hours: float) -> dict[str, Any]:
    canonical = load_corpus_canonical(corpus)
    published = first_published(corpus, canonical)
    per_locale: dict[str, Any] = {}
    for locale in LOCALES:
        rows, strict_ids, provenance, _ = effective_overlays_details(locale, i18n_dir, corpus)
        overdue: list[dict[str, Any]] = []
        grace: list[dict[str, Any]] = []
        complete = 0
        for rid in sorted(canonical):
            status = pair_status(canonical[rid], rows.get(rid), locale, strict=rid in strict_ids,
                                 provenance=provenance.get(rid))
            if is_complete(status):
                complete += 1
                continue
            age_h = max(0.0, (now - published[rid]).total_seconds() / 3600)
            item = {
                "id": rid,
                "state": status["state"],
                "missing": status["missing"],
                "gate": (status["failure"] or {}).get("gate"),
                "first_published_at": utc_text(published[rid]),
                "age_h": round(age_h, 3),
            }
            (overdue if age_h > grace_hours else grace).append(item)
        per_locale[locale] = {
            "stories": len(canonical),
            "complete": complete,
            "backlog": len(overdue),
            "in_grace": len(grace),
            "backlog_ids": [x["id"] for x in overdue],
            "in_grace_ids": [x["id"] for x in grace],
            "items": overdue + grace,
        }
    backlog = any(v["backlog"] for v in per_locale.values())
    waiting = any(v["in_grace"] for v in per_locale.values())
    verdict = "BACKLOG" if backlog else ("GRACE" if waiting else "HEALTHY")
    return {
        "schema": "fcmo-translation-health-v2",
        "stage": "TRANSLATION_HEALTH",
        "verdict": verdict,
        "signal": "BACKLOG" if backlog else "GREEN",
        "checked_at": utc_text(now),
        "grace_hours": grace_hours,
        "scope": "all_corpus",
        "locales": per_locale,
    }


def all_corpus_main(args: argparse.Namespace) -> int:
    try:
        now = resolve_now(args.now)
        payload = corpus_health(args.corpus, args.i18n_dir, now, args.grace_hours)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR {type(exc).__name__}", file=sys.stderr)
        print(str(exc)[:300], file=sys.stderr)
        return 2
    locales = payload["locales"]
    key = "backlog" if payload["verdict"] == "BACKLOG" else "in_grace"
    print(f"{payload['verdict']} " + " ".join(f"{loc}={locales[loc][key]}" for loc in LOCALES))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if payload["verdict"] == "BACKLOG" else 0


def recent_main(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    root = args.root
    stories_path = root / "site" / "data" / "stories.json"
    stories: list[dict[str, Any]] = json.loads(stories_path.read_text(encoding="utf-8"))
    corpus = root / "corpus"
    canonical = load_corpus_canonical(corpus)
    i18n_dir = root / "site" / "data" / "i18n"
    overlays = {locale: effective_overlays_details(locale, i18n_dir, corpus) for locale in LOCALES}
    admission_path = root / 'release-src/data/publication-admission.json'
    if admission_path.is_file():
        # A held update is assessed against its still-published English version;
        # --all-corpus continues to report the incoming version's repair backlog.
        try:
            from tools.native_admission import published_sources
        except ImportError:
            from native_admission import published_sources
        carried = set(json.loads(admission_path.read_text())['carried_ids'])
        selected = published_sources(root / 'release-src')
        for rid in carried:
            canonical[rid] = selected[rid]
        for loc in LOCALES:
            packs, strict_packs, origins, _ = load_locale_details(i18n_dir, loc)
            rows, strict, provenance, _ = overlays[loc]
            for rid in carried:
                rows[rid] = packs.get(rid)
                provenance[rid] = origins.get(rid)
                if rid not in strict_packs:
                    strict.discard(rid)

    watched: list[dict[str, Any]] = []
    overdue: list[dict[str, Any]] = []
    grace: list[dict[str, Any]] = []
    for story in stories:
        rid = str(story.get("research_id") or "")
        published_raw = str(story.get("published_at") or "")
        if not rid or not published_raw:
            continue
        published = parse_time(published_raw)
        age_h = max(0.0, (now - published).total_seconds() / 3600)
        importance = int((story.get("news_value") or {}).get("importance") or 0)
        is_lead = story.get("story_type") == "LEAD"
        if age_h > args.fresh_window_hours or (importance < args.minimum_importance and not is_lead):
            continue
        missing: list[str] = []
        for locale in LOCALES:
            rows, strict_ids, provenance, _ = overlays[locale]
            source = canonical.get(rid)
            if source is None or not is_complete(pair_status(source, rows.get(rid), locale,
                                                              strict=rid in strict_ids,
                                                              provenance=provenance.get(rid))):
                missing.append(locale)
        if not missing:
            continue
        item = {
            "research_id": rid,
            "story_type": story.get("story_type"),
            "importance": importance,
            "published_at": published_raw,
            "age_h": round(age_h, 3),
            "missing": missing,
        }
        watched.append(item)
        (overdue if age_h > args.grace_hours else grace).append(item)

    state = "HEALTHY"
    if overdue:
        state = "UNHEALTHY_TRANSLATION_BACKLOG"
    elif grace:
        state = "DEGRADED_TRANSLATION_GRACE"
    payload = {
        "stage": "TRANSLATION_HEALTH",
        "state": state,
        "target": "complete native es-419 and zh-Hans (every prose field) at publication time",
        "grace_hours": args.grace_hours,
        "fresh_window_hours": args.fresh_window_hours,
        "missing_recent": watched,
        "overdue_count": len(overdue),
        "grace_count": len(grace),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if overdue else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all-corpus", action="store_true", help="measure every live story of --corpus")
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--out", type=Path, default=None, help="also write the JSON payload here")
    parser.add_argument("--now", default=None)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--grace-hours", type=float, default=1.0)
    parser.add_argument("--fresh-window-hours", type=float, default=30.0)
    parser.add_argument("--minimum-importance", type=int, default=4)
    args = parser.parse_args(argv)
    if args.all_corpus:
        return all_corpus_main(args)
    return recent_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
