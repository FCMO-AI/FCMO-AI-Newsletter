#!/usr/bin/env python3
"""Reconcile committed locale overlays with the current canonical public schema.

This is a schema/declassification migration tool, not a translator. When the
airlock deliberately removes a canonical field, old locale packs must not keep
publishing its translated value. The tool prunes only fields/records that no
longer exist in canonical public data; it never invents translations.

The canonical English comes from ``--corpus`` (the committed corpus, preferred)
or, for the legacy pipeline, from the ``fcmo-data`` block of ``--site``.
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


def corpus_records(corpus: Path) -> dict[str, dict[str, Any]]:
    """Live canonical records of the corpus, with the legacy ``why`` alias.

    Locale packs still carry ``why`` next to ``why_it_matters``; the alias keeps
    that field from being pruned as if the canonical record had dropped it.
    """
    try:
        from tools.validate_localizations import load_corpus_canonical
    except ImportError:  # direct script execution from tools/
        from validate_localizations import load_corpus_canonical  # type: ignore[no-redef]
    rows = load_corpus_canonical(corpus)
    if not rows:
        raise SystemExit(f"locale reconciliation: no canonical records in {corpus}")
    out: dict[str, dict[str, Any]] = {}
    for rid, row in rows.items():
        record = dict(row)
        if "why" not in record and "why_it_matters" in record:
            record["why"] = record["why_it_matters"]
        out[rid] = record
    return out


def prune(source: Any, translated: Any) -> Any:
    # Footnote: overlays are sparse by design. We retain translated keys that
    # still exist canonically, and recurse only where both sides have structure.
    if isinstance(source, dict) and isinstance(translated, dict):
        return {key: prune(source[key], value) for key, value in translated.items() if key in source}
    if isinstance(source, list) and isinstance(translated, list):
        if len(source) != len(translated):
            # Dropping the first English item must not associate its translation
            # with the next item, nor retain prose removed at declassification.
            # An empty field stays pending until the editorial writer replaces it.
            return []
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
    parser.add_argument("--corpus", type=Path, default=None, help="canonical corpus directory (preferred over --site)")
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    args = parser.parse_args(argv)

    canonical = corpus_records(args.corpus) if args.corpus else canonical_records(args.site)
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
                if path.name == "part-desk.json" and isinstance(doc.get("provenance"), dict):
                    doc["provenance"] = {rid: meta for rid, meta in doc["provenance"].items()
                                         if rid in new_records and new_records[rid]}
                atomic_json(path, doc, compact="\n" not in original.rstrip("\n"))
                touched += 1
    print(
        f"locale schema reconciliation OK; touched_parts={touched}; "
        f"removed_records={removed_records}; removed_top_level_fields={removed_fields}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
