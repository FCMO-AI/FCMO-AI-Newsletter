#!/usr/bin/env python3
"""Validate native editions truthfully while allowing an explicit translation backlog.

Present ES/ZH overlays receive the same structural and strict Airlock checks as the
legacy validator. Missing overlays are recorded as pending instead of causing the
canonical English newspaper to roll back. Extra/stale locale IDs remain errors.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_localizations import (
    LOCALES,
    check_common,
    check_strict,
    load_locale,
    stable_digest,
    translated_projection,
)
from reconcile_locale_overlays import canonical_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--receipt", type=Path, default=Path("site/data/i18n/integrity-manifest.json"))
    args = parser.parse_args(argv)

    canonical = canonical_records(args.site)
    expected = set(canonical)
    errors: list[str] = []
    receipt_records: dict[str, Any] = {}
    pending_by_locale: dict[str, list[str]] = {}
    strict_pairs = 0
    historical_pairs = 0

    for locale in LOCALES:
        rows, strict_ids = load_locale(args.i18n_dir, locale)
        stale = set(rows) - expected
        if stale:
            errors.append(f"{locale}: stale/non-canonical ids {sorted(stale)}")
        pending_by_locale[locale] = sorted(expected - set(rows))
        for rid in sorted(expected & set(rows)):
            overlay = rows[rid]
            if not isinstance(overlay, dict):
                errors.append(f"{locale}:{rid}: overlay must be object")
                continue
            if rid in strict_ids:
                check_strict(canonical[rid], overlay, locale, rid, errors)
                tier = "strict_airlock"
                strict_pairs += 1
            else:
                check_common(canonical[rid], overlay, locale, rid, errors)
                tier = "historical_structural"
                historical_pairs += 1
            receipt_records.setdefault(rid, {})[locale] = {
                "canonical_digest": stable_digest(translated_projection(canonical[rid])),
                "locale_digest": stable_digest(overlay),
                "validation_tier": tier,
            }

    # ARB emits ES/ZH deltas as one editorial unit. A differing backlog would mean
    # one native edition silently drifted away from the other and is not accepted.
    if pending_by_locale[LOCALES[0]] != pending_by_locale[LOCALES[1]]:
        errors.append("ES/ZH pending-translation ID sets differ")

    if errors:
        raise SystemExit("localization integrity FAILED:\n" + "\n".join(f"- {x}" for x in errors))

    pending = pending_by_locale[LOCALES[0]]
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "fcmo-locale-integrity-v3",
        "canonical_locale": "en",
        "required_locales": list(LOCALES),
        "editorial_owner": "ARB publication agent for native editions; pending translations are explicit",
        "human_reviewed": False,
        "network_translation": False,
        "strict_airlock_pairs": strict_pairs,
        "historical_structural_pairs": historical_pairs,
        "canonical_story_count": len(expected),
        "native_complete_story_count": len(expected) - len(pending),
        "pending_translation_count": len(pending),
        "pending_translation_ids": pending,
        "state": "COMPLETE" if not pending else "DEGRADED_TRANSLATION_BACKLOG",
        "records": receipt_records,
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"localization integrity OK; stories={len(expected)}; native_complete={len(expected)-len(pending)}; "
        f"pending={len(pending)}; state={receipt['state']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
