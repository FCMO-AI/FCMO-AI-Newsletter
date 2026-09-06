#!/usr/bin/env python3
"""Refresh locale-pack metadata after the canonical public corpus changes.

This tool never writes translated prose. It updates only the canonical record count
and canonical editorial digest carried by locale metadata/parts so the existing
hash-verified localization assembler can distinguish a current pack from stale input.
ARB remains the sole author of new or materially changed ES/ZH story wording.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tools.apply_curated_i18n import _canonical_digest, _canonical_editorial
except ImportError:  # direct execution from tools/
    from apply_curated_i18n import _canonical_digest, _canonical_editorial

LOCALES = ("es-419", "zh-Hans")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    args = parser.parse_args(argv)

    index = args.site / "index.html"
    if not index.is_file():
        raise SystemExit(f"locale identity: canonical index missing: {index}")
    canonical = _canonical_editorial(index.read_text(encoding="utf-8"))
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
