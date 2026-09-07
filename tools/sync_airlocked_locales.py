#!/usr/bin/env python3
"""Merge ARB-authored public locale deltas into Newsletter locale overlays.

The private research/editorial agent owns EN/es-419/zh-Hans story wording before the
airlock. Newsletter is a deterministic sink: it may validate, merge and publish those
editions, but it never asks a model provider to translate or rewrite them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

LOCALES = ("es-419", "zh-Hans")
SCHEMA = "fcmo-airlocked-locale-delta-v1"
PART_SCHEMA = "fcmo-curated-locale-part-v1"
AIRLOCK_PART = "part-airlock.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_existing(locale_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Path]]:
    records: dict[str, dict[str, Any]] = {}
    owners: dict[str, Path] = {}
    for path in sorted(locale_dir.glob("part-*.json")):
        doc = read_json(path)
        rows = doc.get("records")
        if not isinstance(rows, dict):
            raise SystemExit(f"{path}: records object missing")
        for rid, overlay in rows.items():
            if rid in records:
                raise SystemExit(f"{locale_dir}: duplicate locale record {rid}")
            if not isinstance(overlay, dict):
                raise SystemExit(f"{path}: {rid} overlay must be an object")
            records[rid] = overlay
            owners[rid] = path
    return records, owners


def merge_overlay(base: Any, delta: Any) -> Any:
    """Overlay sparse refreshed prose without deleting still-valid curated siblings."""
    # Footnote: an Airlock delta means "these paths were freshly authored", not
    # "delete every path omitted from this object". Dictionaries therefore merge
    # recursively; lists/scalars replace atomically because item-wise list merging
    # could silently mismatch claims, limitations or evidence gaps.
    if isinstance(base, dict) and isinstance(delta, dict):
        merged = dict(base)
        for key, value in delta.items():
            merged[key] = merge_overlay(base.get(key), value) if key in base else value
        return merged
    return delta


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    args = parser.parse_args(argv)

    changed = added = promoted = 0
    for locale in LOCALES:
        incoming_path = args.corpus / "data" / "locales" / locale / "records.json"
        if not incoming_path.is_file():
            # Footnote: an absent *delta* is valid for a quiet release. Completeness
            # is proven later against the canonical story set, so a newly arriving
            # untranslated story still fails closed rather than becoming English-only.
            print(f"{locale}: no airlocked locale delta")
            continue
        incoming = read_json(incoming_path)
        if incoming.get("schema") != SCHEMA or incoming.get("locale") != locale:
            raise SystemExit(f"{incoming_path}: invalid locale-delta contract")
        rows = incoming.get("records")
        if not isinstance(rows, dict):
            raise SystemExit(f"{incoming_path}: records object missing")

        locale_dir = args.i18n_dir / locale
        locale_dir.mkdir(parents=True, exist_ok=True)
        existing, owners = load_existing(locale_dir)
        airlock_part = locale_dir / AIRLOCK_PART
        if airlock_part.is_file():
            airlock_doc = read_json(airlock_part)
            airlock_rows = airlock_doc.get("records")
            if not isinstance(airlock_rows, dict):
                raise SystemExit(f"{airlock_part}: records object missing")
        else:
            airlock_doc = {
                "schema": PART_SCHEMA,
                "locale": locale,
                "canonical_locale": "en",
                "generated_from": "ARB airlock; editorial wording authored upstream",
                "records": {},
            }
            airlock_rows = airlock_doc["records"]

        touched: dict[Path, dict[str, Any]] = {}
        for rid, overlay in sorted(rows.items()):
            if not isinstance(rid, str) or not rid.startswith("FCMO-") or not isinstance(overlay, dict):
                raise SystemExit(f"{incoming_path}: malformed record {rid!r}")
            owner = owners.get(rid)
            prior = existing.get(rid)
            merged = merge_overlay(prior, overlay) if isinstance(prior, dict) else overlay
            if owner is None:
                added += 1
            elif owner != airlock_part:
                # Footnote: once ARB republishes a historical ID, move that ID out
                # of its grandfathered pack into part-airlock. Its complete curated
                # prose is preserved underneath the sparse fresh delta so provenance
                # upgrades do not accidentally erase reader-visible translations.
                doc = touched.setdefault(owner, read_json(owner))
                doc["records"].pop(rid, None)
                promoted += 1
            elif prior != merged:
                changed += 1
            airlock_rows[rid] = merged

        for path, doc in touched.items():
            write_json(path, doc)
        if rows or airlock_rows:
            write_json(airlock_part, airlock_doc)

    print(f"airlocked locale sync OK; updated={changed}; added={added}; promoted_from_history={promoted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
