#!/usr/bin/env python3
"""Verify provider-free native-edition integrity plus the production health SLO.

ARB owns native prose; Newsletter imports it, validates every present ES/ZH overlay
strictly, and records any candidate/source backlog explicitly. The bounded grace below
is an observability/reconciliation rule for production health, **not** permission to
release a partial EN-only Story. `LOCALIZATION.md` remains authoritative: Pages release
eligibility requires complete native Story coverage through the separate strict gate.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def fail(label: str, proc: subprocess.CompletedProcess[str]) -> int:
    print(f"{label} FAILED", file=sys.stderr)
    print((proc.stdout or "")[-2500:], file=sys.stderr)
    print((proc.stderr or "")[-2500:], file=sys.stderr)
    return 1


def main() -> int:
    # Never rewrite the committed integrity receipt just to test it.
    with tempfile.TemporaryDirectory(prefix="fcmo-locale-oracle-") as tmp:
        receipt = Path(tmp) / "integrity.json"
        structural = run(
            "tools/validate_localizations_partial.py",
            "--site", "release-src",
            "--i18n-dir", "site/data/i18n",
            "--receipt", str(receipt),
        )
        if structural.returncode:
            return fail("integridad de ediciones nativas/backlog", structural)
        doc = json.loads(receipt.read_text(encoding="utf-8"))
        if doc.get("schema") != "fcmo-locale-integrity-v3":
            print("integrity receipt schema inesperado", file=sys.stderr)
            return 1
        pending = doc.get("pending_translation_ids") or []
        if doc.get("pending_translation_count") != len(pending):
            print("translation backlog count no coincide con sus IDs", file=sys.stderr)
            return 1
        if doc.get("state") not in {"COMPLETE", "DEGRADED_TRANSLATION_BACKLOG"}:
            print(f"estado de traduccion inesperado: {doc.get('state')!r}", file=sys.stderr)
            return 1

    # Footnote: this is a health/prioritization SLO, not the release gate. A recent
    # material backlog should become operationally loud after one hour, while the
    # strict Pages path independently requires all Story IDs to have both native
    # editions before a candidate may be published.
    health = run(
        "tools/translation_health.py",
        "--grace-hours", "1",
        "--fresh-window-hours", "30",
        "--minimum-importance", "4",
    )
    if health.returncode:
        return fail("salud de traduccion reciente", health)

    print(
        f"traduccion OK: {doc.get('native_complete_story_count')} completas; "
        f"pending={doc.get('pending_translation_count')}; recientes materiales dentro del SLO"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
