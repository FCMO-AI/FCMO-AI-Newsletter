#!/usr/bin/env python3
"""Verify cached independent language-editor approvals against current public bytes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.review_translations import LOCALES, digest, merged_locale
from tools.translate_records import _read_canonical, _source_overlay


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--ledger", type=Path, default=Path("site/data/i18n/review-ledger.json"))
    args = parser.parse_args()

    # Footnote: the historical release predates independent review receipts. The strict
    # requirement activates with the same autonomous-newsroom status marker as the rest
    # of Airlock v2, avoiding a fake retroactive claim that older translations were
    # independently reviewed when they were not.
    if not (args.site / "data" / "newsroom-status.json").is_file():
        print("translation review gate: migration release; strict receipt not yet activated")
        return 0
    if not args.ledger.is_file():
        print("translation review gate FAILED: review-ledger.json is missing")
        return 1
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    reviews = ledger.get("reviews") if isinstance(ledger, dict) else None
    if ledger.get("schema_version") != 1 or not isinstance(reviews, dict):
        print("translation review gate FAILED: invalid ledger schema")
        return 1
    canonical, _index = _read_canonical(args.site)
    errors: list[str] = []
    for locale in LOCALES:
        translated = merged_locale(args.i18n_dir, locale)
        if set(translated) != set(canonical):
            errors.append(f"{locale}: translation IDs differ from canonical")
            continue
        for identifier in sorted(canonical):
            key = f"{locale}:{identifier}"
            receipt = reviews.get(key) or {}
            expected_source = digest(_source_overlay(canonical[identifier]))
            expected_translation = digest(translated[identifier])
            if receipt.get("decision") != "PASS":
                errors.append(f"{key}: no PASS review")
            if receipt.get("source_digest") != expected_source:
                errors.append(f"{key}: source digest changed after review")
            if receipt.get("translation_digest") != expected_translation:
                errors.append(f"{key}: translation digest changed after review")
            if int(receipt.get("mqm_major") or 0) != 0 or int(receipt.get("mqm_critical") or 0) != 0:
                errors.append(f"{key}: non-zero major/critical review count")
    if errors:
        print("translation review gate FAILED")
        for error in errors[:30]:
            print("-", error)
        if len(errors) > 30:
            print(f"- ... {len(errors)-30} more")
        return 1
    print(f"translation review gate OK; approvals={len(LOCALES) * len(canonical)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
