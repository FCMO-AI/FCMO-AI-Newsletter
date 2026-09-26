#!/usr/bin/env python3
"""Validate native editions truthfully while allowing an explicit translation backlog.

English publication fails open; each locale fails closed. Every (story, locale)
pair is classified field by field (see ``validate_localizations.pair_status``):

* complete (``NATIVE_ARB``) pairs publish natively;
* ``PENDING`` pairs (no overlay, or an overlay that lacks any prose field the
  English record has, such as a headline-only delta) are recorded as backlog;
* ``FAILED`` pairs (English left in place, changed numbers/IDs/URLs, broken
  structure) are recorded with the gate that rejected them.

Pending and failed pairs never make the English newspaper roll back; they are
rendered as a localized notice by ``mark_pending_localizations.py``. Overlays for
ids that are not canonical remain errors: they would publish text for a story
that does not exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tools.validate_localizations import (
        LOCALES,
        is_complete,
        load_locale,
        pair_status,
        stable_digest,
        translated_projection,
    )
    from tools.reconcile_locale_overlays import canonical_records
except ImportError:  # direct script execution from tools/
    from validate_localizations import (
        LOCALES,
        is_complete,
        load_locale,
        pair_status,
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
    failed_by_locale: dict[str, dict[str, str]] = {}
    strict_pairs = 0
    historical_pairs = 0

    for locale in LOCALES:
        rows, strict_ids = load_locale(args.i18n_dir, locale)
        stale = set(rows) - expected
        if stale:
            errors.append(f"{locale}: stale/non-canonical ids {sorted(stale)}")
        pending: list[str] = []
        failed: dict[str, str] = {}
        for rid in sorted(expected):
            overlay = rows.get(rid)
            strict = rid in strict_ids
            status = pair_status(canonical[rid], overlay, locale, strict=strict)
            if status["state"] == "FAILED":
                failed[rid] = status["failure"]["gate"]
            elif not is_complete(status):
                pending.append(rid)
            if isinstance(overlay, dict):
                tier = "strict_airlock" if strict else "historical_structural"
                if strict:
                    strict_pairs += 1
                else:
                    historical_pairs += 1
                receipt_records.setdefault(rid, {})[locale] = {
                    "canonical_digest": stable_digest(translated_projection(canonical[rid])),
                    "locale_digest": stable_digest(overlay),
                    "validation_tier": tier,
                    "state": status["state"],
                    "missing": status["missing"],
                }
        pending_by_locale[locale] = pending
        failed_by_locale[locale] = failed

    if errors:
        raise SystemExit("localization integrity FAILED:\n" + "\n".join(f"- {x}" for x in errors))

    # A story is natively complete only when every locale is complete.
    incomplete = sorted(
        set().union(*(set(p) for p in pending_by_locale.values()))
        | set().union(*(set(f) for f in failed_by_locale.values()))
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "fcmo-locale-integrity-v3",
        "canonical_locale": "en",
        "required_locales": list(LOCALES),
        "editorial_owner": "FCMO Publication Desk for native editions; pending translations are explicit",
        "human_reviewed": False,
        "network_translation": False,
        "strict_airlock_pairs": strict_pairs,
        "historical_structural_pairs": historical_pairs,
        "canonical_story_count": len(expected),
        "native_complete_story_count": len(expected) - len(incomplete),
        "pending_translation_count": len(incomplete),
        "pending_translation_ids": incomplete,
        "pending_by_locale": pending_by_locale,
        "failed_by_locale": failed_by_locale,
        "state": "COMPLETE" if not incomplete else "DEGRADED_TRANSLATION_BACKLOG",
        "records": receipt_records,
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    per_locale = " ".join(
        f"{loc}:pending={len(pending_by_locale[loc])},failed={len(failed_by_locale[loc])}" for loc in LOCALES
    )
    print(
        f"localization integrity OK; stories={len(expected)}; native_complete={len(expected) - len(incomplete)}; "
        f"pending={len(incomplete)}; {per_locale}; state={receipt['state']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
