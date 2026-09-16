#!/usr/bin/env python3
"""Verify the provider-free native-edition publication contract.

ARB owns native prose; Newsletter imports it, validates present ES/ZH overlays
structurally, and may record an explicit candidate/source backlog for operations.
Publication itself is stricter: `LOCALIZATION.md` defines each EN/ES/ZH Story set as
one release obligation, so this oracle requires complete native Story identity coverage
with no health-SLO grace. The separate production-health workflow owns reconciliation
SLOs; it does not redefine release eligibility.
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

    # Footnote: this oracle is intentionally stricter than production-health
    # prioritization. A source backlog can be represented truthfully for diagnosis,
    # but the publication test itself must not convert a health grace window into
    # permission to ship an incomplete native-edition Story set.
    release_gate = run("tools/translation_health.py", "--require-complete")
    if release_gate.returncode:
        return fail("ediciones nativas incompletas para publicacion", release_gate)

    print(
        f"traduccion OK: {doc.get('native_complete_story_count')} completas; "
        f"pending={doc.get('pending_translation_count')}; release_gate=COMPLETE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
