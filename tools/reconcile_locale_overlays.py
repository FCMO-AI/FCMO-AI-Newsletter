#!/usr/bin/env python3
"""Reconcile committed locale overlays with the current canonical public schema.

This is a schema/declassification migration tool, not a translator. When the
airlock deliberately removes a canonical field, old locale packs must not keep
publishing its translated value. The tool prunes only fields/records that no
longer exist in canonical public data; it never invents translations.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
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
        raise SystemExit("locale reconciliation: canonical fcmo-data missing")
    value = json.loads(match.group(1))
    rows = value.get("records")
    if not isinstance(rows, list):
        raise SystemExit("locale reconciliation: canonical records missing")
    return {row["id"]: row for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}


def prune(source: Any, translated: Any) -> Any:
    # Footnote: overlays are sparse by design. We retain translated keys that
    # still exist canonically, and recurse only where both sides have structure.
    if isinstance(source, dict) and isinstance(translated, dict):
        return {key: prune(source[key], value) for key, value in translated.items() if key in source}
    if isinstance(source, list) and isinstance(translated, list):
        return [prune(s, t) for s, t in zip(source, translated)]
    return translated


def atomic_json(path: Path, value: dict[str, Any], compact: bool) -> None:
    text = (
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
        if compact
        else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent,
        prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    args = parser.parse_args(argv)

    canonical = canonical_records(args.site)
    removed_records = removed_fields = touched = 0
    for locale in ("es-419", "zh-Hans"):
        locale_dir = args.i18n_dir / locale
        for path in sorted(locale_dir.glob("part-*.json")):
            original = path.read_text(encoding="utf-8")
            doc = json.loads(original)
            records = doc.get("records")
            if not isinstance(records, dict):
                raise SystemExit(f"{path}: records object missing")
            new_records: dict[str, Any] = {}
            changed = False
            for rid, overlay in records.items():
                source = canonical.get(rid)
                if source is None:
                    removed_records += 1
                    changed = True
                    continue
                pruned = prune(source, overlay)
                if pruned != overlay:
                    # Count top-level removals as a useful operator signal while
                    # preserving nested behavior without fragile bookkeeping.
                    if isinstance(overlay, dict) and isinstance(pruned, dict):
                        removed_fields += len(set(overlay) - set(pruned))
                    changed = True
                new_records[rid] = pruned
            if changed:
                doc["records"] = new_records
                atomic_json(path, doc, compact="\n" not in original.rstrip("\n"))
                touched += 1
    print(
        f"locale schema reconciliation OK; touched_parts={touched}; "
        f"removed_records={removed_records}; removed_top_level_fields={removed_fields}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
