#!/usr/bin/env python3
"""Refresh locale-pack metadata after the canonical public corpus changes.

This tool never writes translated prose. It updates only the canonical record count
and canonical editorial digest carried by locale metadata/parts so the existing
hash-verified localization assembler can distinguish a current pack from stale input.
ARB remains the sole author of new or materially changed ES/ZH story wording.

The digest is sha256 of ``{id: {title, summary, why_it_matters}}`` serialized with
sorted keys (the identity the curated-i18n assembler used), taken from
``--corpus`` when given, else from the ``fcmo-data`` block of ``--site``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

LOCALES = ("es-419", "zh-Hans")
REQUIRED_FIELDS = ("title", "summary", "why_it_matters")
FCMO_DATA = re.compile(r'<script id="fcmo-data" type="application/json">(.*?)</script>', re.S)


def _editorial(rows: Any, origin: str) -> dict[str, dict[str, str]]:
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{origin}: canonical corpus contains no records")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
            raise ValueError(f"{origin}: canonical corpus contains a malformed record")
        if row["id"] in result:
            raise ValueError(f"{origin}: duplicate record id {row['id']}")
        missing = [f for f in REQUIRED_FIELDS if not isinstance(row.get(f), str) or not row[f].strip()]
        if missing:
            raise ValueError(f"{origin}: record {row['id']} is missing {', '.join(missing)}")
        result[row["id"]] = {field: row[field] for field in REQUIRED_FIELDS}
    return result


def _canonical_editorial(index_text: str) -> dict[str, dict[str, str]]:
    """Editorial identity fields from a legacy page's embedded ``fcmo-data``."""
    match = FCMO_DATA.search(index_text)
    if not match:
        raise ValueError("index is missing embedded fcmo-data corpus")
    return _editorial(json.loads(match.group(1)).get("records"), "fcmo-data")


def corpus_editorial(corpus: Path) -> dict[str, dict[str, str]]:
    """Editorial identity fields of the live canonical corpus records."""
    try:
        from tools.validate_localizations import load_corpus_canonical
    except ImportError:  # direct script execution from tools/
        from validate_localizations import load_corpus_canonical  # type: ignore[no-redef]
    rows = load_corpus_canonical(corpus)
    return _editorial([dict(row, id=rid) for rid, row in sorted(rows.items())], str(corpus))


def _canonical_digest(canonical: dict[str, dict[str, str]]) -> str:
    return hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--corpus", type=Path, default=None, help="canonical corpus directory (preferred over --site)")
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    args = parser.parse_args(argv)

    try:
        if args.corpus:
            canonical = corpus_editorial(args.corpus)
        else:
            index = args.site / "index.html"
            if not index.is_file():
                raise SystemExit(f"locale identity: canonical index missing: {index}")
            canonical = _canonical_editorial(index.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(f"locale identity: {exc}") from exc
    digest = _canonical_digest(canonical)
    count = len(canonical)
    touched = 0

    for locale in LOCALES:
        locale_dir = args.i18n_dir / locale
        ui_path = locale_dir / "ui.json"
        if not ui_path.is_file():
            raise SystemExit(f"locale identity: missing UI catalogue {ui_path}")
        ui = read_json(ui_path)
        ui["canonical_record_count"] = count
        ui["canonical_source_sha256"] = digest
        curation = ui.setdefault("curation", {})
        # Footnote: this metadata is descriptive, not a claim of human review.
        # Replacing the old provider-era wording keeps the current source tree
        # truthful while preserving the explicit runtime/human-review booleans.
        curation["method"] = "arb-agent-authored-source-controlled"
        curation["human_reviewed"] = False
        curation["runtime_machine_translation"] = False
        write_json(ui_path, ui)
        touched += 1

        parts = sorted(locale_dir.glob("part-*.json"))
        if not parts:
            raise SystemExit(f"locale identity: {locale} has no locale parts")
        for path in parts:
            doc = read_json(path)
            if doc.get("schema") != "fcmo-curated-locale-part-v1" or doc.get("locale") != locale:
                raise SystemExit(f"locale identity: invalid locale part metadata: {path}")
            doc["canonical_source_sha256"] = digest
            write_json(path, doc)
            touched += 1

    print(f"locale identity OK; records={count}; digest={digest}; files={touched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
