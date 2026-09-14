#!/usr/bin/env python3
"""Run the existing synthetic-story refresh through the production locale contract.

The historical E2E oracle remains useful: it creates a new story plus ARB-authored
ES/ZH deltas and proves that ingestion, Story surfaces, discovery, overlay and final
publication gates all carry it through. Its one stale assumption was invoking the
retired all-stories-at-once localization gate. Production now validates every native
edition that exists while representing missing editions explicitly as pending.

This adapter changes only that stage and also proves the real daily workflow contains
the pending-page step. It deliberately reuses all of the original end-to-end output
assertions, including that the synthetic story with supplied native prose appears in
EN/ES/ZH.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import verificar_refresco as legacy


def main() -> int:
    workflow = (ROOT / ".github" / "workflows" / "daily-refresh.yml").read_text(encoding="utf-8")
    required = (
        "tools/validate_localizations_partial.py --site release-src",
        "tools/mark_pending_localizations.py --site site",
        "tools/ingest_corpus.py --corpus corpus --out release-src",
    )
    missing = [value for value in required if value not in workflow]
    if missing:
        print("daily-refresh no refleja el contrato de produccion: " + ", ".join(missing), file=sys.stderr)
        return 1
    if "tools/validate_localizations.py --site release-src" in workflow:
        print("daily-refresh volvio accidentalmente al gate sincrono estricto", file=sys.stderr)
        return 1

    original = legacy.corre

    def production_corre(cwd: Path, nombre: str, args: list[str]) -> bool:
        if args and args[0] == "tools/validate_localizations.py":
            args = ["tools/validate_localizations_partial.py", *args[1:]]
            nombre = "integridad de locales disponibles + deuda explicita"
        return original(cwd, nombre, args)

    legacy.corre = production_corre
    try:
        return legacy.main()
    finally:
        legacy.corre = original


if __name__ == "__main__":
    raise SystemExit(main())
