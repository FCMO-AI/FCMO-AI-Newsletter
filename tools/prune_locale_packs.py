#!/usr/bin/env python3
"""Remove locale-overlay fields that no longer exist in canonical public English.

The semantic airlock can deliberately retract a previously public field from the public
contract. Locale packs must follow that declassification inward; otherwise stale
translations could keep publishing prose that English no longer contains. This tool
only deletes overlay keys that are absent from the current canonical record and never
invents or rewrites translations.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCRIPT_RE = re.compile(
    r'<script\s+id=["\']fcmo-data["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.S | re.I,
)


def canonical_records(site: Path) -> dict[str, dict[str, Any]]:
    text = (site / "index.html").read_text(encoding="utf-8")
    match = SCRIPT_RE.search(text)
    if not match:
        raise ValueError("canonical index has no fcmo-data corpus")
    rows = json.loads(match.group(1)).get("records")
    if not isinstance(rows, list):
        raise ValueError("canonical fcmo-data contains no records list")
    return {row["id"]: row for row in rows}


def prune(source: Any, overlay: Any) -> Any:
    if isinstance(source, dict) and isinstance(overlay, dict):
        return {
            key: prune(source[key], value)
            for key, value in overlay.items()
            if key in source
        }
    if isinstance(source, list) and isinstance(overlay, list):
        return [
            prune(source[index], value)
            for index, value in enumerate(overlay[: len(source)])
        ]
    return overlay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--locales", default="es-419,zh-Hans")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    canonical = canonical_records(args.site)
    removed = 0
    touched = 0
    for locale in [item.strip() for item in args.locales.split(",") if item.strip()]:
        for path in sorted((args.i18n_dir / locale).glob("part-*.json")):
            original = json.loads(path.read_text(encoding="utf-8"))
            document = json.loads(json.dumps(original, ensure_ascii=False))
            records = document.get("records") or {}
            for record_id, overlay in list(records.items()):
                if record_id not in canonical:
                    # Footnote: whole-record removal is intentionally not automatic.
                    # A missing canonical ID is a stronger contract change and should
                    # remain visible to the normal exact-ID publication gate.
                    continue
                before = json.dumps(overlay, ensure_ascii=False, sort_keys=True)
                after_obj = prune(canonical[record_id], overlay)
                after = json.dumps(after_obj, ensure_ascii=False, sort_keys=True)
                if before != after:
                    before_keys = set(overlay) if isinstance(overlay, dict) else set()
                    after_keys = set(after_obj) if isinstance(after_obj, dict) else set()
                    removed += len(before_keys - after_keys)
                    records[record_id] = after_obj
            if document != original:
                touched += 1
                if args.apply:
                    compact = "\n" not in path.read_text(encoding="utf-8").rstrip("\n")
                    text = (
                        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
                        if compact
                        else json.dumps(document, ensure_ascii=False, indent=2) + "\n"
                    )
                    path.write_text(text, encoding="utf-8")
    print(json.dumps({"touched_parts": touched, "removed_top_level_fields": removed, "applied": args.apply}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
