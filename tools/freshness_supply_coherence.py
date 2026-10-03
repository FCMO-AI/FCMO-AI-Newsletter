#!/usr/bin/env python3
"""Observe whether Newsletter story staleness is caused by upstream supply or representation.

This tool is deliberately EVIDENCE_ONLY. It does not publish, block Pages, reinterpret
ARB evidence, or decide release eligibility. It separates three facts that are easy to
collapse incorrectly: the age of the material Story layer, whether a newer sanitized
published edition exists upstream, and whether that edition is bound to stable canonical
Story identities with native-edition coverage.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
NUMBERED_SECTION = re.compile(r"^\s*\d+[.)]\s+")
PUBLISHED_AT = re.compile(r"\bPublished\s+(\d{4}-\d{2}-\d{2}T[^\s]+)")
LOCALES = ("es-419", "zh-Hans")
SCHEMA = "fcmo-newsletter-freshness-supply-coherence-v1"
AUTHORITY = "EVIDENCE_ONLY"


class CoherenceError(ValueError):
    """Raised when the observer cannot establish a trustworthy input shape."""


def parse_time(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def story_time(story: dict[str, Any]) -> datetime | None:
    return parse_time(story.get("modified_at")) or parse_time(story.get("published_at"))


def importance(story: dict[str, Any]) -> int:
    try:
        return int((story.get("news_value") or {}).get("importance") or 0)
    except (TypeError, ValueError):
        return 0


def age_hours(now: datetime, value: datetime | None) -> float | None:
    if value is None:
        return None
    return max(0.0, (now - value).total_seconds() / 3600.0)


def edition_published_at(edition: dict[str, Any]) -> datetime | None:
    direct = parse_time(edition.get("published_at"))
    if direct is not None:
        return direct
    # Footnote: ingest_corpus currently preserves publication time inside the public
    # edition preamble rather than as a first-class field. Parsing this explicit
    # public-safe receipt text keeps the observer compatible without pretending the
    # date alone is an exact timestamp. A future schema field automatically wins.
    for block in edition.get("preamble") or []:
        if not isinstance(block, dict):
            continue
        match = PUBLISHED_AT.search(str(block.get("text") or ""))
        if match:
            parsed = parse_time(match.group(1))
            if parsed is not None:
                return parsed
    return None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def locale_ids(root: Path, locale: str) -> set[str]:
    result: set[str] = set()
    directory = root / locale
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("part-*.json")):
        doc = load_json(path)
        rows = doc.get("records") if isinstance(doc, dict) else None
        if not isinstance(rows, dict):
            raise CoherenceError(f"{path}: records object missing")
        result.update(str(key) for key in rows)
    return result


def latest_published_edition(memory: list[dict[str, Any]]) -> dict[str, Any] | None:
    published = [
        row for row in memory
        if isinstance(row, dict) and row.get("published") is True and str(row.get("date") or "")
    ]
    if not published:
        return None
    return max(published, key=lambda row: str(row.get("date") or ""))


def observe(
    *,
    stories_path: Path,
    publication_memory_path: Path,
    editions_dir: Path,
    locales_root: Path,
    now: datetime,
    acceptable_hours: float,
    minimum_importance: int,
) -> dict[str, Any]:
    stories = load_json(stories_path)
    memory = load_json(publication_memory_path)
    if not isinstance(stories, list) or not all(isinstance(row, dict) for row in stories):
        raise CoherenceError("stories must be an array of objects")
    if not isinstance(memory, list) or not all(isinstance(row, dict) for row in memory):
        raise CoherenceError("publication memory must be an array of objects")

    material = [
        row for row in stories
        if importance(row) >= minimum_importance and story_time(row) is not None
    ]
    newest_story = max(material, key=lambda row: story_time(row) or datetime.min.replace(tzinfo=timezone.utc)) if material else None
    newest_story_time = story_time(newest_story) if newest_story else None
    newest_story_age = age_hours(now, newest_story_time)

    memory_edition = latest_published_edition(memory)
    detail = memory_edition
    if memory_edition is not None:
        path = editions_dir / f"{memory_edition['date']}.json"
        if path.is_file():
            loaded = load_json(path)
            if not isinstance(loaded, dict):
                raise CoherenceError(f"{path}: edition must be an object")
            detail = loaded

    edition_time = edition_published_at(detail or {}) if detail else None
    edition_age = age_hours(now, edition_time)
    sections = [
        row for row in ((detail or {}).get("sections") or [])
        if isinstance(row, dict)
    ]
    signal_sections = [
        row for row in sections
        if NUMBERED_SECTION.match(str(row.get("title") or ""))
    ]
    related_ids = sorted({
        str(value)
        for value in ((detail or {}).get("related_brief_ids") or [])
        if isinstance(value, str) and PUBLIC_ID.fullmatch(value)
    })
    locale_sets = {locale: locale_ids(locales_root, locale) for locale in LOCALES}
    missing_locales = {
        rid: [locale for locale in LOCALES if rid not in locale_sets[locale]]
        for rid in related_ids
    }
    missing_locales = {rid: missing for rid, missing in missing_locales.items() if missing}

    story_fresh = newest_story_age is not None and newest_story_age <= acceptable_hours
    publication_newer = (
        edition_time is not None
        and newest_story_time is not None
        and edition_time > newest_story_time
    )
    publication_recent = edition_age is not None and edition_age <= acceptable_hours

    if story_fresh:
        state = "STORY_SUPPLY_FRESH"
    elif memory_edition is None or edition_time is None:
        state = "STORY_STALE_UPSTREAM_PUBLICATION_UNKNOWN"
    elif not publication_newer or not publication_recent:
        state = "STORY_STALE_NO_NEWER_RECENT_PUBLICATION"
    elif signal_sections and not related_ids:
        state = "UPSTREAM_PUBLICATION_NEWER_UNBOUND"
    elif related_ids and missing_locales:
        state = "UPSTREAM_PUBLICATION_NEWER_BOUND_UNLOCALIZED"
    elif related_ids:
        state = "UPSTREAM_PUBLICATION_NEWER_BOUND_AND_LOCALIZED"
    else:
        state = "UPSTREAM_PUBLICATION_NEWER_NO_SIGNAL_SECTIONS"

    # Footnote: even BOUND_AND_LOCALIZED is deliberately not called "eligible".
    # Identity + locale coverage are necessary representation prerequisites, not proof
    # that evidence/importance/editorial policy authorizes front-page use. Release law
    # remains project-owned and must be reviewed separately.
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "state": state,
        "story_supply": {
            "acceptable_hours": acceptable_hours,
            "minimum_importance": minimum_importance,
            "newest_material_story_id": (newest_story or {}).get("research_id"),
            "newest_material_story_at": newest_story_time.isoformat().replace("+00:00", "Z") if newest_story_time else None,
            "newest_material_story_age_h": round(newest_story_age, 6) if newest_story_age is not None else None,
            "fresh": story_fresh,
        },
        "upstream_publication": {
            "date": (memory_edition or {}).get("date"),
            "published_at": edition_time.isoformat().replace("+00:00", "Z") if edition_time else None,
            "age_h": round(edition_age, 6) if edition_age is not None else None,
            "newer_than_story_supply": publication_newer,
            "recent_within_acceptable_window": publication_recent,
            "numbered_signal_sections": len(signal_sections),
            "related_brief_ids": related_ids,
        },
        "representation": {
            "stable_related_story_ids": bool(related_ids),
            "missing_native_locales_by_id": missing_locales,
            "all_related_ids_native_complete": bool(related_ids) and not missing_locales,
        },
        "claim_boundary": {
            "release_gate_implication": "NONE",
            "notes": [
                "A stale Story layer is a production-health fact, not automatically a release-blocking prerequisite.",
                "A newer published edition proves newer public publication material exists; it does not by itself prove Story eligibility.",
                "Stable identity, native-edition coverage, evidence class, materiality and editorial authorization remain separate prerequisites.",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stories", type=Path, default=Path("site/data/stories.json"))
    parser.add_argument("--publication-memory", type=Path, default=Path("release-src/data/publication-memory.json"))
    parser.add_argument("--editions-dir", type=Path, default=Path("release-src/data/editions"))
    parser.add_argument("--locales-root", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--acceptable-hours", type=float, default=48.0)
    parser.add_argument("--minimum-importance", type=int, default=4)
    parser.add_argument("--now", help="Optional timezone-aware ISO timestamp for deterministic replay")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        raise SystemExit("--now must be a valid timezone-aware ISO timestamp")
    try:
        result = observe(
            stories_path=args.stories,
            publication_memory_path=args.publication_memory,
            editions_dir=args.editions_dir,
            locales_root=args.locales_root,
            now=now,
            acceptable_hours=args.acceptable_hours,
            minimum_importance=args.minimum_importance,
        )
    except (OSError, json.JSONDecodeError, CoherenceError) as exc:
        print(f"freshness supply coherence FAILED: {exc}")
        return 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    # Footnote: observational states intentionally return zero. This tool supplies
    # evidence to health/Proof Spine review; it never becomes a hidden release gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
