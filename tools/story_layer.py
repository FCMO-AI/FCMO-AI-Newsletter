#!/usr/bin/env python3
"""Build the v2 story layer (contracts/stories.v2.schema.json) from the corpus.

One story per public id, including withdrawn and merged ids, which change status
and never disappear. Inputs:

* ``corpus/data/developments.jsonl``   upstream records, normalized per record by
  tools/taxonomy.py; a record that cannot be normalized is quarantined (stderr
  ``QUARANTINE <id> <codes>``), never fatal for the batch.
* ``corpus/carried.jsonl``             records kept live by the corpus guard
  (``carried_forward: true``).
* ``corpus/tombstones.json``           withdrawals and merges, each with a public
  correction. Reinstating a story is one data change: set ``reinstated_at``.
* ``corpus/first-published.json``      frozen first publication time, URL date,
  slug and merge redirect per id. Ids that are not frozen yet take the earliest
  ``published_at`` in the git history of ``site/data/stories.json`` (full clones
  only), else the currently published value, else the build time.
* ``corpus/data/locales/*/records.json`` and ``site/data/i18n`` locale editions.

Headlines and deks are never produced by cutting text: the headline is the whole
title when it fits (8-90 characters) and the dek is the whole first sentence of
the summary when it fits (20-240); otherwise the story is not front-page eligible.

    story_layer.py build  --corpus corpus --history-git . --out stories.json [--now ISO]
    story_layer.py ledger --corpus corpus --history-git . [--now ISO] [--check]

Standard library only.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

try:
    from tools import taxonomy
    from tools import corpus_guard
    from tools.validate_localizations import load_locale_details
except ImportError:  # executed as tools/story_layer.py
    import taxonomy  # type: ignore
    import corpus_guard  # type: ignore
    from validate_localizations import load_locale_details  # type: ignore

STORIES_SCHEMA = "fcmo-stories-v2"
LEDGER_SCHEMA = "fcmo-first-published-v1"
LOCALES = ("en", "es-419", "zh-Hans")
TARGET_LOCALES = ("es-419", "zh-Hans")
SLUG_MAX = 72
MX_OFFSET = timedelta(hours=-6)  # America/Mexico_City has had no DST since 2022.
STORIES_PATH = "site/data/stories.json"
CORPUS_RECORDS_PATH = "corpus/data/developments.jsonl"
L10N_FIELDS = (
    "title", "summary", "why_it_matters", "importance_rationale", "technical",
    "evidence.claims", "evidence.limitations", "evidence.gaps", "evidence.contradictory", "related",
)
MERGE_CORRECTION = {
    "en": "This story covered the same development as another report and was merged into it.",
    "es-419": "Esta historia cubría el mismo hecho que otra nota y se integró en ella.",
    "zh-Hans": "本文与另一篇报道涉及同一事项，已并入该报道。",
}
REINSTATEMENT_CORRECTION = {
    "en": "Reinstated. This story was verified again and returned to the live edition.",
    "es-419": "Restablecida. Esta historia se verificó de nuevo y volvió a la edición en vivo.",
    "zh-Hans": "已恢复。本文经重新核实后已回到在线版本。",
}
UPSTREAM_WITHDRAWAL_CORRECTION = {
    "es-419": "Retirada por el flujo de investigación. No se proporcionó más detalle público con el retiro.",
    "zh-Hans": "已由研究数据流撤回。撤回时未提供更多公开说明。",
}


def log(line: str) -> None:
    print(line, file=sys.stderr)


# ---------------------------------------------------------------------------------------
# Time, dates and slugs
# ---------------------------------------------------------------------------------------
def resolve_now(flag: str | None = None) -> str:
    return corpus_guard.resolve_now(flag)


def parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def mx_date(stamp: str) -> str:
    """America/Mexico_City calendar date of a UTC timestamp."""
    return (parse_utc(stamp) + MX_OFFSET).date().isoformat()


def story_slug(title: str) -> str:
    return taxonomy.slugify(title, SLUG_MAX) or "story"


# ---------------------------------------------------------------------------------------
# Git history (read only)
# ---------------------------------------------------------------------------------------
def _git(repo: Path, *args: str) -> bytes | None:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def is_full_history(repo: Path | None) -> bool:
    if repo is None:
        return False
    out = _git(repo, "rev-parse", "--is-shallow-repository")
    return out is not None and out.strip() == b"false"


def file_versions(repo: Path, rel: str) -> list[str]:
    """Commits that touched ``rel``, newest first."""
    out = _git(repo, "log", "--format=%H", "--", rel)
    return out.decode().split() if out else []


def show(repo: Path, commit: str, rel: str) -> bytes | None:
    return _git(repo, "show", f"{commit}:{rel}")


def _published_times(data: Any) -> dict[str, str]:
    """research_id -> published_at (UTC seconds) of a v1 site/data/stories.json list."""
    out: dict[str, str] = {}
    for row in data if isinstance(data, list) else []:
        if not isinstance(row, dict):
            continue
        rid = row.get("research_id") or row.get("id")
        stamp = taxonomy.utc_seconds(row.get("published_at"))
        if isinstance(rid, str) and taxonomy.PUBLIC_ID.fullmatch(rid) and stamp:
            out[rid] = stamp
    return out


def history_first_published(repo: Path) -> dict[str, str]:
    """Earliest published_at per id across the git history of the published story data."""
    return dict(_history_first_published(str(Path(repo).resolve())))


@functools.lru_cache(maxsize=4)
def _history_first_published(repo_key: str) -> tuple[tuple[str, str], ...]:
    repo = Path(repo_key)
    first: dict[str, str] = {}
    for commit in file_versions(repo, STORIES_PATH):
        blob = show(repo, commit, STORIES_PATH)
        try:
            data = json.loads(blob) if blob else None
        except ValueError:
            continue
        for rid, stamp in _published_times(data).items():
            if rid not in first or stamp < first[rid]:
                first[rid] = stamp
    return tuple(sorted(first.items()))


def current_published(site: Path | None) -> dict[str, str]:
    path = site / "data" / "stories.json" if site else None
    if path is None or not path.is_file():
        return {}
    try:
        return _published_times(json.loads(path.read_text(encoding="utf-8")))
    except ValueError:
        return {}


def history_records(repo: Path, wanted: Iterable[str]) -> dict[str, dict[str, Any]]:
    """Last committed corpus record for each wanted id (newest version that has it)."""
    need = set(wanted)
    found: dict[str, dict[str, Any]] = {}
    if not need:
        return found
    for commit in file_versions(repo, CORPUS_RECORDS_PATH):
        blob = show(repo, commit, CORPUS_RECORDS_PATH)
        for line in (blob or b"").decode("utf-8", "replace").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            rid = row.get("id") if isinstance(row, dict) else None
            if rid in need and rid not in found:
                found[rid] = row
        if need <= set(found):
            break
    return found


# ---------------------------------------------------------------------------------------
# Corpus inputs
# ---------------------------------------------------------------------------------------
def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_ledger(corpus: Path) -> dict[str, Any]:
    doc = read_json(corpus / "first-published.json")
    if not isinstance(doc, dict) or doc.get("schema") != LEDGER_SCHEMA or not isinstance(doc.get("entries"), dict):
        return {"schema": LEDGER_SCHEMA, "entries": {}}
    return doc


def load_tombstones(corpus: Path) -> dict[str, Any]:
    doc = read_json(corpus / "tombstones.json")
    if not isinstance(doc, dict) or not isinstance(doc.get("tombstones"), list):
        return {"schema": corpus_guard.TOMBSTONES_SCHEMA, "tombstones": []}
    return doc


def load_locale_deltas(corpus: Path) -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for locale in TARGET_LOCALES:
        doc = read_json(corpus / "data" / "locales" / locale / "records.json", {})
        rows = doc.get("records") if isinstance(doc, dict) else None
        out[locale] = {k: v for k, v in (rows or {}).items() if isinstance(v, dict)}
    return out


def load_site_packs(i18n: Path | None) -> dict[str, dict[str, dict[str, Any]]]:
    """Published editions with field provenance, including desk gap fills."""
    out: dict[str, dict[str, dict[str, Any]]] = {loc: {} for loc in TARGET_LOCALES}
    if i18n is None or not i18n.is_dir():
        return out
    manifest = read_json(i18n / "integrity-manifest.json", {}) or {}
    listed = manifest.get("records") if isinstance(manifest, dict) else None
    for locale in TARGET_LOCALES:
        rows, _, origins, _ = load_locale_details(i18n, locale)
        for rid, row in rows.items():
            if isinstance(row, dict) and isinstance(listed, dict) and locale in (listed.get(rid) or {}):
                out[locale][rid] = {**row, "_provenance": origins.get(rid, {})}
    return out


# ---------------------------------------------------------------------------------------
# First publication and merges
# ---------------------------------------------------------------------------------------
def first_published_map(ids: Iterable[str], ledger: dict[str, Any], repo: Path | None,
                        site: Path | None, now: str | None) -> dict[str, str]:
    """Frozen ledger value, else full git history, else the live stories.json, else ``now``."""
    entries = ledger.get("entries", {})
    history = history_first_published(repo) if is_full_history(repo) else {}
    live = current_published(site)
    out: dict[str, str] = {}
    for rid in ids:
        if rid in entries:
            out[rid] = entries[rid]["first_published_at"]
        elif rid in history:
            out[rid] = history[rid]
        elif rid in live:
            out[rid] = live[rid]
        elif now is not None:
            out[rid] = now
    return out


def _lead_url(record: dict[str, Any]) -> str:
    url = (record.get("source_urls") or [""])[0]
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    return f"{host}{parts.path.rstrip('/')}" + (f"?{parts.query}" if parts.query else "")


def find_duplicates(records: dict[str, dict[str, Any]], first_published: dict[str, str],
                    blocked: Iterable[str] = ()) -> dict[str, str]:
    """{duplicate id: surviving id} for stories that report one development.

    Two records are one development when they cite the same lead source and share
    an organization. The earliest published story survives. Ids in ``blocked``
    (reinstated after a merge) are never merged automatically again.
    """
    blocked = set(blocked)
    groups: dict[str, list[str]] = {}
    for rid, record in records.items():
        key = _lead_url(record)
        if key:
            groups.setdefault(key, []).append(rid)
    merges: dict[str, str] = {}
    far = "9999-12-31T23:59:59Z"
    for ids in groups.values():
        if len(ids) < 2:
            continue
        ordered = sorted(ids, key=lambda i: (first_published.get(i, far), records[i]["event_at"], i))
        survivor = ordered[0]
        orgs = {o.casefold() for o in records[survivor].get("organizations", [])}
        for rid in ordered[1:]:
            if rid in blocked:
                continue
            if orgs & {o.casefold() for o in records[rid].get("organizations", [])}:
                merges[rid] = survivor
    return merges


def tombstone_index(doc: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    """(active entries by id, ids whose entry was reinstated)."""
    active: dict[str, dict[str, Any]] = {}
    reinstated: set[str] = set()
    for entry in doc.get("tombstones", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        if entry.get("reinstated_at") is None:
            active[entry["id"]] = entry
        else:
            reinstated.add(entry["id"])
    return active, reinstated


# ---------------------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------------------
def _texts(values: Any, key: str | None = None) -> list[str] | None:
    if not isinstance(values, list):
        return None
    out = []
    for item in values:
        text = item.get(key or "text") if isinstance(item, dict) else item
        if not isinstance(text, str) or not text.strip():
            return None
        out.append(text.strip())
    return out


def _gap_texts(values: Any) -> list[str] | None:
    return _texts(values, "description")


def locale_fields(row: dict[str, Any], story: dict[str, Any], derived_headline: bool,
                  derived_dek: bool) -> dict[str, Any]:
    """Map one localized record onto story l10n field paths (only complete fields)."""
    fields: dict[str, Any] = {}
    for key, source in (("title", "title"), ("summary", "summary"), ("importance_rationale", "importance_rationale")):
        value = row.get(source)
        if isinstance(value, str) and value.strip():
            fields[key] = value.strip()
    why = row.get("why_it_matters") or row.get("why")
    if isinstance(why, str) and why.strip():
        fields["why_it_matters"] = why.strip()
        if "importance_rationale" not in fields:
            fields["importance_rationale"] = why.strip()
    technical = row.get("technical")
    english_technical = story.get("technical") or {}
    if isinstance(technical, dict) and english_technical and all(
            isinstance(technical.get(k), str) and technical[k].strip() for k in english_technical):
        fields["technical"] = {k: technical[k].strip() for k in english_technical}
    evidence = story["evidence"]
    for path, source, reader, english in (
        ("evidence.claims", "claims", _texts, evidence["claims"]),
        ("evidence.limitations", "limitations", _texts, evidence["limitations"]),
        ("evidence.gaps", "evidence_gaps", _gap_texts, evidence["gaps"]),
        ("evidence.contradictory", "contradictory_evidence", _texts, evidence["contradictory"]),
    ):
        values = reader(row.get(source))
        if values is not None and len(values) == len(english) and values:
            fields[path] = values
    if any(item.get("summary") for item in story.get("related", [])):
        localized_relationships = {
            (item.get("target_id"), item.get("type")): item
            for item in row.get("relationships", []) if isinstance(item, dict)
        }
        related = []
        for item in story["related"]:
            localized = localized_relationships.get((item.get("id"), item.get("type")), {})
            value = {key: item[key] for key in ("id", "type") if key in item}
            if item.get("summary") and isinstance(localized.get("summary"), str) and localized["summary"].strip():
                value["summary"] = localized["summary"].strip()
            related.append(value)
        if related:
            fields["related"] = related
    headline = row.get("headline")
    if isinstance(headline, str) and 1 <= len(headline.strip()) <= taxonomy.HEADLINE_MAX:
        fields["headline"] = headline.strip()
    elif derived_headline and "title" in fields:
        value = taxonomy.derive_headline(fields["title"])
        if value:
            fields["headline"] = value
    dek = row.get("dek")
    if isinstance(dek, str) and 1 <= len(dek.strip()) <= taxonomy.DEK_MAX:
        fields["dek"] = dek.strip()
    elif derived_dek and "summary" in fields:
        value = taxonomy.derive_dek(fields["summary"])
        if value:
            fields["dek"] = value
    return fields


def build_l10n(story: dict[str, Any], sources: list[dict[str, Any]], derived_headline: bool,
               derived_dek: bool) -> dict[str, Any]:
    required = list(L10N_FIELDS)
    # The paper already uses localized title/summary when a short headline/dek
    # cannot be derived. Those optional display variants are not new prose debt.
    english_empty = {
        "technical": not story.get("technical"),
        "importance_rationale": not story.get("importance_rationale"),
        "evidence.claims": not story["evidence"]["claims"],
        "evidence.limitations": not story["evidence"]["limitations"],
        "evidence.gaps": not story["evidence"]["gaps"],
        "evidence.contradictory": not story["evidence"]["contradictory"],
        "related": not any(item.get("summary") for item in story.get("related", [])),
    }
    flat: dict[str, Any] = {}
    origins: dict[str, str | None] = {}
    source_keys = {"evidence.claims": "claims", "evidence.limitations": "limitations",
                   "evidence.gaps": "evidence_gaps", "evidence.contradictory": "contradictory_evidence",
                   "headline": "headline", "dek": "dek", "related": "relationships"}
    for row in sources:
        for path, value in locale_fields(row, story, derived_headline, derived_dek).items():
            if path not in flat:
                flat[path] = value
                source_key = source_keys.get(path, path)
                if path == "headline" and "headline" not in row:
                    source_key = "title"
                if path == "dek" and "dek" not in row:
                    source_key = "summary"
                if path == "importance_rationale" and "importance_rationale" not in row:
                    source_key = "why_it_matters" if "why_it_matters" in row else "why"
                meta = (row.get("_provenance") or {}).get(source_key) or {}
                origins[path] = meta.get("origin") if isinstance(meta, dict) else meta
    missing = [p for p in required if p not in flat and not english_empty.get(p, False)]
    if "related" not in missing:
        translated = {
            (item.get("target_id"), item.get("type")): item
            for row in sources for item in row.get("relationships", []) if isinstance(item, dict)
        }
        relationship_summaries_missing = any(
            item.get("summary") and not (
                isinstance(translated.get((item.get("id"), item.get("type")), {}).get("summary"), str)
                and translated[(item.get("id"), item.get("type"))]["summary"].strip()
            )
            for item in story.get("related", [])
        )
        if relationship_summaries_missing:
            missing.append("related")
    fields: dict[str, Any] = {}
    for path, value in flat.items():
        if path not in required and path not in {"headline", "dek"}:
            continue
        if path.startswith("evidence."):
            kind = path.split(".", 1)[1]
            box = fields.setdefault("evidence", {})
            if kind == "claims":
                box[kind] = [{"text": t} for t in value]
            elif kind == "gaps":
                box[kind] = [{"description": t} for t in value]
            else:
                box[kind] = value
        else:
            fields[path] = value
    provided = [p for p in required if p in flat]
    selected_origins = {origins.get(p) for p in provided}
    bad_origin = bool(selected_origins - {"arb", "publication-desk"})
    entry: dict[str, Any] = {
        "state": "FAILED" if bad_origin else ("PENDING" if missing else
                 ("MACHINE_REVIEWED" if "publication-desk" in selected_origins else "NATIVE_ARB")),
        "fields": fields,
        "missing": missing,
    }
    if provided:
        entry["provenance"] = {p: origins.get(p) for p in provided if origins.get(p) is not None}
    return entry


# ---------------------------------------------------------------------------------------
# Story objects
# ---------------------------------------------------------------------------------------
def sources_of(record: dict[str, Any]) -> list[dict[str, Any]]:
    declared = {s["url"]: s for s in record.get("sources") or []}
    out = []
    for url in record["source_urls"]:
        domain = taxonomy.source_domain(url)
        if not re.fullmatch(r"[a-z0-9.-]+", domain):
            continue
        primary = declared[url]["primary"] if url in declared else taxonomy.is_primary_source(url)
        out.append({"url": url, "domain": domain, "primary": bool(primary)})
    return out


def media_for(rid: str, title: str, beat: str, site: Path | None) -> dict[str, Any] | None:
    """The publication-owned explainer graphic when it exists on the site, else null."""
    if site is None:
        return None
    for rel in (f"assets/story-media/{rid}.svg", f"assets/explainers/{beat}.svg"):
        path = site / rel
        if not path.is_file():
            continue
        width, height = 1600, 900
        head = path.read_text(encoding="utf-8", errors="replace")[:2000]
        box = re.search(r'viewBox="\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)\s*"', head)
        if box:
            width, height = max(1, int(float(box.group(1)))), max(1, int(float(box.group(2))))
        return {
            "kind": "explainer",
            "local_path": rel,
            "credit": "FCMO AI Research Desk",
            "license": "FCMO original editorial graphic",
            "alt": {"en": f"FCMO explainer graphic: {title}"},
            "width": width,
            "height": height,
        }
    return None


def story_object(record: dict[str, Any], ledger_entry: dict[str, Any], carried: bool, site: Path | None,
                 locale_rows: list[dict[str, Any]]) -> dict[str, Any]:
    headline = record.get("headline") or taxonomy.derive_headline(record["title"])
    dek = record.get("dek") or taxonomy.derive_dek(record["summary"])
    story: dict[str, Any] = {
        "id": record["id"],
        "slug": ledger_entry["slug"],
        "url_date": ledger_entry["url_date"],
        "kind": record["kind"],
        "status": "live",
        "beat": record["beat"],
        "desk": record["primary_desk"],
        "title": record["title"],
    }
    if headline:
        story["headline"] = headline
    if dek:
        story["dek"] = dek
    story.update({
        "summary": record["summary"],
        "why_it_matters": record["why_it_matters"],
        "importance_rationale": record["importance_rationale"],
    })
    if record.get("technical"):
        story["technical"] = record["technical"]
    story.update({
        "event_at": record["event_at"],
        "date_precision": record["date_precision"],
    })
    if record["kind"] == "event":
        story["scheduled_at"] = record["scheduled_at"]
    story.update({
        "first_published_at": ledger_entry["first_published_at"],
        "updated_at": ledger_entry["first_published_at"],
        "importance": record["importance_effective_score"],
        "evidence_class": record["evidence_class"],
        "confidence": record["confidence"],
        "front_page_eligible": bool(headline and dek),
        "carried_forward": carried,
        "evidence": {
            "claims": [{k: c[k] for k in ("label", "qualifier", "text") if k in c} for c in record["claims"]],
            "limitations": list(record["limitations"]),
            "gaps": [{"kind": g["kind"], "description": g["description"]} for g in record["evidence_gaps"]],
            "contradictory": list(record["contradictory_evidence"]),
        },
        "sources": sources_of(record),
        "corrections": [],
        "related": [],
        "organizations": list(record["organizations"]),
        "topics": list(record["topics"]),
        "regions": list(record["regions"]),
        "media": media_for(record["id"], record["title"], record["beat"], site),
    })
    story["l10n"] = {loc: build_l10n(story, locale_rows_for(loc, locale_rows), not record.get("headline"),
                                     not record.get("dek")) for loc in TARGET_LOCALES}
    return story


def locale_rows_for(locale: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r[locale] for r in rows if isinstance(r.get(locale), dict)]


def correction(at: str, kind: str, reason: str, text: dict[str, str]) -> dict[str, Any]:
    return {"at": at, "kind": kind, "reason_code": reason,
            "text": {k: v for k, v in text.items() if k in LOCALES and isinstance(v, str) and v.strip()}}


# ---------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------
def load_previous_stories(site: Path) -> dict[str, Any] | None:
    path = site / "data" / "stories.v2.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    except ValueError:
        return None
    return doc if isinstance(doc, dict) and doc.get("schema") == STORIES_SCHEMA else None


def record_from_story(story: dict[str, Any]) -> dict[str, Any]:
    """The normalized-record view of a previously published story (no history needed)."""
    evidence = story.get("evidence") or {}
    record: dict[str, Any] = {
        "id": story["id"], "kind": story.get("kind", "development"), "status": "active",
        "title": story["title"], "summary": story["summary"], "why_it_matters": story["why_it_matters"],
        "importance_rationale": story.get("importance_rationale") or story["why_it_matters"],
        "beat": story["beat"], "primary_desk": story["desk"], "desks": [story["desk"]],
        "event_at": story["event_at"], "date_precision": story["date_precision"],
        "evidence_class": story["evidence_class"], "confidence": story["confidence"],
        "importance_effective_score": story["importance"],
        "claims": list(evidence.get("claims") or []),
        "limitations": list(evidence.get("limitations") or []),
        "evidence_gaps": [dict(g) for g in evidence.get("gaps") or []],
        "contradictory_evidence": list(evidence.get("contradictory") or []),
        "organizations": list(story.get("organizations") or []),
        "topics": list(story.get("topics") or []),
        "regions": list(story.get("regions") or []),
        "source_urls": [s["url"] for s in story.get("sources") or []],
        "sources": [{"url": s["url"], "primary": bool(s.get("primary"))} for s in story.get("sources") or []],
        "relationships": [{"target_id": r["id"], "type": r["type"], **({"summary": r["summary"]} if r.get("summary") else {})}
                          for r in story.get("related") or [] if r.get("type") in {"related", "follow_up"}],
    }
    for key in ("technical", "headline", "dek", "scheduled_at"):
        if story.get(key):
            record[key] = story[key]
    return record


def locale_rows_from_story(story: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Previous per-locale fields in the record shape build_l10n reads."""
    rows: dict[str, dict[str, Any]] = {}
    for locale in TARGET_LOCALES:
        fields = ((story.get("l10n") or {}).get(locale) or {}).get("fields") or {}
        evidence = fields.get("evidence") or {}
        row = {k: fields[k] for k in ("title", "summary", "why_it_matters", "importance_rationale",
                                       "technical", "headline", "dek") if k in fields}
        if "claims" in evidence:
            row["claims"] = [c.get("text") for c in evidence["claims"]]
        if "limitations" in evidence:
            row["limitations"] = list(evidence["limitations"])
        if "gaps" in evidence:
            row["evidence_gaps"] = [g.get("description") for g in evidence["gaps"]]
        if "contradictory" in evidence:
            row["contradictory_evidence"] = list(evidence["contradictory"])
        old_origins = ((story.get("l10n") or {}).get(locale) or {}).get("provenance") or {}
        reverse = {"evidence.claims": "claims", "evidence.limitations": "limitations",
                   "evidence.gaps": "evidence_gaps", "evidence.contradictory": "contradictory_evidence"}
        row["_provenance"] = {reverse.get(path, path): {"origin": origin}
                              for path, origin in old_origins.items()}
        rows[locale] = row
    return rows


class StoryInputs:
    """Everything the story layer reads, loaded once."""

    def __init__(self, corpus: Path, repo: Path | None, site: Path | None, i18n: Path | None, now: str,
                 previous: dict[str, Any] | None = None):
        self.corpus, self.repo, self.site, self.now = corpus, repo, site, now
        if previous is None and site is not None:
            previous = load_previous_stories(site)
        rows = corpus_guard.read_records(corpus)
        self.carried_rows = corpus_guard.read_carried(corpus)
        self.tombstones = load_tombstones(corpus)
        self.ledger = load_ledger(corpus)
        self.active, self.reinstated = tombstone_index(self.tombstones)
        current_ids = {r["id"] for r in rows}
        carried = [c["record"] for c in self.carried_rows if c["id"] not in current_ids]
        self.carried_ids = {c["id"] for c in self.carried_rows if c["id"] not in current_ids}
        # Previously published ids that left the corpus (withdrawn, or dropped before the
        # guard existed) keep their last committed record.
        known = current_ids | self.carried_ids
        wanted = (set(self.ledger["entries"]) | set(self.active)) - known
        if repo is not None and is_full_history(repo):
            wanted |= set(history_first_published(repo)) - known
        historical = history_records(repo, wanted) if repo is not None else {}
        # A shallow checkout has no history: the previous stories.v2 output keeps the
        # last published form of every id that left the corpus.
        before = {s["id"]: s for s in (previous or {}).get("stories", []) if isinstance(s, dict) and s.get("id")}
        frozen = {rid: before[rid] for rid in wanted - set(historical) if rid in before}
        self.unavailable = sorted(wanted - set(historical) - set(frozen))
        self.orphans = (set(historical) | set(frozen)) - set(self.active)
        self.records: dict[str, dict[str, Any]] = {}
        self.quarantined: list[tuple[str, list[str]]] = []
        for row in rows + carried + list(historical.values()):
            try:
                record = taxonomy.normalize_record(row)
            except taxonomy.Quarantine as exc:
                self.quarantined.append((row.get("id", "-"), exc.codes))
                continue
            self.records.setdefault(record["id"], record)
        for rid, story in frozen.items():
            self.records.setdefault(rid, record_from_story(story))
        self.first = first_published_map(self.records, self.ledger, repo, site, now)
        deltas = load_locale_deltas(corpus)
        packs = load_site_packs(i18n)
        self.locale_rows = {
            rid: [{loc: ({**deltas[loc][rid], "_provenance": {key: {"origin": "arb"} for key in deltas[loc][rid]}}
                        if rid in deltas[loc] else None) for loc in TARGET_LOCALES},
                  {loc: packs[loc].get(rid) for loc in TARGET_LOCALES}]
            + ([locale_rows_from_story(frozen[rid])] if rid in frozen else [])
            for rid in self.records
        }
        self.release_id = corpus_guard.read_release_id(corpus)

    def merges(self) -> tuple[dict[str, str], dict[str, str]]:
        """(recorded merges, detected-but-unrecorded merges), each {duplicate: survivor}."""
        recorded: dict[str, str] = {}
        for rid, entry in self.active.items():
            if entry.get("action") == "superseded" and entry.get("superseded_by") in self.records:
                recorded[rid] = entry["superseded_by"]
        for rid, entry in self.ledger["entries"].items():
            target = entry.get("redirect_to")
            if target in self.records and rid not in self.reinstated and rid not in recorded:
                recorded[rid] = target
        for rid, record in self.records.items():
            upstream = (record.get("withdrawal") or {}).get("superseded_by")
            if record["status"] == "superseded" and upstream in self.records and rid not in recorded:
                recorded[rid] = upstream
        withdrawn = {rid for rid, e in self.active.items() if e.get("action") == "withdrawn"}
        live = {rid: r for rid, r in self.records.items()
                if rid not in recorded and rid not in withdrawn and r["status"] not in corpus_guard.WITHDRAWN_STATUSES}
        detected = {d: s for d, s in find_duplicates(live, self.first, self.reinstated).items() if d not in recorded}
        return recorded, detected

    def ledger_entry(self, rid: str) -> dict[str, Any]:
        entry = self.ledger["entries"].get(rid)
        if entry:
            return entry
        stamp = self.first[rid]
        return {"first_published_at": stamp, "url_date": mx_date(stamp), "slug": story_slug(self.records[rid]["title"])}


def resolve_target(rid: str, merges: dict[str, str]) -> str:
    seen = {rid}
    while rid in merges and merges[rid] not in seen:
        rid = merges[rid]
        seen.add(rid)
    return rid


def build_stories(inputs: StoryInputs) -> dict[str, Any]:
    recorded, detected = inputs.merges()
    merges = {**detected, **recorded}
    for dup, survivor in sorted(detected.items()):
        log(f"MERGE_UNRECORDED {dup} -> {survivor}")
    for rid, codes in inputs.quarantined:
        log(f"QUARANTINE {rid} {','.join(codes)}")
    for rid in sorted(inputs.orphans):
        log(f"ALERT STORY_ORPHAN {rid} (published before, absent from the corpus without a tombstone)")
    for rid in inputs.unavailable:
        log(f"ALERT STORY_RECORD_UNAVAILABLE {rid} (no corpus record, no git history, no previous stories.v2)")
    stories: dict[str, dict[str, Any]] = {}
    for rid, record in inputs.records.items():
        carried = rid in inputs.carried_ids or rid in inputs.orphans
        stories[rid] = story_object(record, inputs.ledger_entry(rid), carried, inputs.site, inputs.locale_rows[rid])
    for rid, story in stories.items():
        record = inputs.records[rid]
        corrections: list[dict[str, Any]] = []
        for entry in inputs.tombstones.get("tombstones", []):
            if entry.get("id") != rid or entry.get("reinstated_at") is None:
                continue
            kind = "merge" if entry.get("action") == "superseded" else "withdrawal"
            corrections.append(correction(entry["withdrawn_at"], kind, entry["reason_code"], entry["correction"]))
            corrections.append(correction(entry["reinstated_at"], "reinstatement", "REINSTATED", REINSTATEMENT_CORRECTION))
        tomb = inputs.active.get(rid)
        if rid in merges:
            target = resolve_target(rid, merges)
            story["status"] = "merged"
            story["merged_into"] = target
            if tomb:
                corrections.append(correction(tomb["withdrawn_at"], "merge", tomb["reason_code"], tomb["correction"]))
            else:
                at = (record.get("withdrawal") or {}).get("at") if record["status"] == "superseded" else None
                corrections.append(correction(at or inputs.now, "merge", "DUPLICATE", MERGE_CORRECTION))
            story["related"].append({"id": target, "type": "duplicate_of"})
            stories[target]["related"].append({"id": rid, "type": "supersedes"})
        elif tomb:
            story["status"] = "withdrawn"
            corrections.append(correction(tomb["withdrawn_at"], "withdrawal", tomb["reason_code"], tomb["correction"]))
        elif record["status"] in corpus_guard.WITHDRAWN_STATUSES:
            story["status"] = "withdrawn"
            block = record["withdrawal"]
            text = {"en": block["note"]}
            if block["note"] == taxonomy.GENERIC_WITHDRAWAL_NOTE:
                text.update(UPSTREAM_WITHDRAWAL_CORRECTION)
            corrections.append(correction(block["at"], "withdrawal", block["reason_code"], text))
        if story["status"] != "live":
            story["front_page_eligible"] = False
            story["carried_forward"] = False
        story["corrections"] = sorted(corrections, key=lambda c: c["at"])
        stamps = [story["first_published_at"]] + [c["at"] for c in story["corrections"]]
        story["updated_at"] = max(stamps)
    for rid, story in stories.items():
        known = {r["id"] for r in story["related"]}
        for rel in inputs.records[rid].get("relationships", []):
            target = rel["target_id"]
            if target in stories and target not in known and target != rid:
                item = {"id": target, "type": rel["type"]}
                if rel.get("summary"):
                    item["summary"] = rel["summary"]
                story["related"].append(item)
                known.add(target)
    # Relationships are resolved after initial story objects are formed. Rebuild
    # locale state now so any reader-facing relationship summaries are covered
    # and carried in the v2 story object just like evidence prose.
    for rid, story in stories.items():
        record = inputs.records[rid]
        rows = inputs.locale_rows[rid]
        story["l10n"] = {
            locale: build_l10n(story, locale_rows_for(locale, rows), not record.get("headline"), not record.get("dek"))
            for locale in TARGET_LOCALES
        }
    ordered = sorted(stories.values(), key=lambda s: (s["first_published_at"], s["id"]), reverse=True)
    return {
        "schema": STORIES_SCHEMA,
        "generated_at": inputs.now,
        "release_id": inputs.release_id,
        "canonical_locale": "en",
        "locales": list(LOCALES),
        "stories": ordered,
    }


# ---------------------------------------------------------------------------------------
# Ledger maintenance (first-published.json and merge tombstones)
# ---------------------------------------------------------------------------------------
def update_ledger(corpus: Path, repo: Path | None, site: Path | None, now: str) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Freeze first publication for every published id and record detected merges.

    Returns (ledger, tombstones, change lines). Only ids that were really
    published (in the git history or in the live stories.json) are frozen; an id
    never published stays unfrozen until it is.
    """
    inputs = StoryInputs(corpus, repo, site, None, now)
    ledger = {"schema": LEDGER_SCHEMA, "entries": dict(inputs.ledger["entries"])}
    tombstones = {"schema": corpus_guard.TOMBSTONES_SCHEMA, "tombstones": list(inputs.tombstones["tombstones"])}
    history = history_first_published(repo) if is_full_history(repo) else {}
    live = current_published(site)
    changes: list[str] = []
    for rid in sorted(inputs.records):
        if rid in ledger["entries"]:
            continue
        stamp = history.get(rid) or live.get(rid)
        if not stamp:
            continue
        ledger["entries"][rid] = {"first_published_at": stamp, "url_date": mx_date(stamp),
                                  "slug": story_slug(inputs.records[rid]["title"])}
        changes.append(f"LEDGER {rid} {stamp}")
    recorded, detected = inputs.merges()
    tombstoned = {e["id"] for e in tombstones["tombstones"]}
    for dup, survivor in sorted(detected.items()):
        if dup in tombstoned or dup not in ledger["entries"] or survivor not in ledger["entries"]:
            continue
        tombstones["tombstones"].append({
            "id": dup,
            "action": "superseded",
            "withdrawn_at": now,
            "reason_code": "DUPLICATE",
            "decided_by": "editorial_policy",
            "correction": dict(MERGE_CORRECTION),
            "superseded_by": survivor,
            "reinstated_at": None,
        })
        changes.append(f"MERGE {dup} -> {survivor}")
    for dup, survivor in {**detected, **recorded}.items():
        entry = ledger["entries"].get(dup)
        if entry is not None and "redirect_to" not in entry and dup not in inputs.reinstated:
            if dup in {e["id"] for e in tombstones["tombstones"]} or dup in recorded:
                entry = dict(entry)
                entry["redirect_to"] = survivor
                ledger["entries"][dup] = entry
                changes.append(f"REDIRECT {dup} -> {survivor}")
    ledger["entries"] = dict(sorted(ledger["entries"].items()))
    return ledger, tombstones, changes


def write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def default_site(corpus: Path) -> Path | None:
    site = corpus.resolve().parent / "site"
    return site if site.is_dir() else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "ledger"):
        p = sub.add_parser(name)
        p.add_argument("--corpus", type=Path, required=True)
        p.add_argument("--history-git", type=Path, help="git work tree whose history dates first publication")
        p.add_argument("--site", type=Path, help="published site root (default: <corpus>/../site)")
        p.add_argument("--now")
        if name == "build":
            p.add_argument("--out", type=Path, required=True)
            p.add_argument("--i18n", type=Path, help="published locale packs (default: <site>/data/i18n)")
        else:
            p.add_argument("--check", action="store_true", help="print the changes without writing")
    args = parser.parse_args(argv)
    try:
        now = resolve_now(args.now)
        site = args.site if args.site is not None else default_site(args.corpus)
        if args.command == "build":
            i18n = args.i18n if args.i18n is not None else (site / "data" / "i18n" if site else None)
            document = build_stories(StoryInputs(args.corpus, args.history_git, site, i18n, now))
            write_json_atomic(args.out, document)
            counts: dict[str, int] = {}
            for story in document["stories"]:
                counts[story["status"]] = counts.get(story["status"], 0) + 1
            print("stories OK " + " ".join(f"{k}={counts.get(k, 0)}" for k in ("live", "withdrawn", "merged"))
                  + f" front_page={sum(s['front_page_eligible'] for s in document['stories'])}")
            return 0
        ledger, tombstones, changes = update_ledger(args.corpus, args.history_git, site, now)
        for line in changes:
            print(line)
        if not args.check and changes:
            write_json_atomic(args.corpus / "first-published.json", ledger)
            write_json_atomic(args.corpus / "tombstones.json", tombstones)
        print(f"ledger OK entries={len(ledger['entries'])} changes={len(changes)}")
        return 0
    except corpus_guard.GuardInputError as exc:
        log(f"USAGE {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
