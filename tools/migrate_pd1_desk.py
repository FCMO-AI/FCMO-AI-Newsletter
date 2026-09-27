#!/usr/bin/env python3
"""Move PD1's exact changed values to the desk pack and restore ARB bytes.

The baseline is the pre-PD1 airlock commit. Refuse to run on unexpected input;
this is a one-time, auditable migration, not a translation generator.
"""
import json
import subprocess
from pathlib import Path

BASE = "c4ad8f2"
AT = "2026-09-27T00:54:13Z"  # PD1 ledger T_end; exact per-field times were not recorded.


def main() -> None:
    for locale in ("es-419", "zh-Hans"):
        airlock = Path("site/data/i18n") / locale / "part-airlock.json"
        original = subprocess.check_output(["git", "show", f"{BASE}:{airlock}"])
        before = json.loads(original)
        current = json.loads(airlock.read_bytes())
        if set(current["records"]) != set(before["records"]):
            raise SystemExit(f"{locale}: record membership changed; refusing migration")
        changed = {}
        for rid, old in before["records"].items():
            new = current["records"][rid]
            if set(old) - set(new):
                raise SystemExit(f"{locale}:{rid}: ARB field removed; refusing migration")
            delta = {key: value for key, value in new.items() if old.get(key) != value}
            if delta:
                changed[rid] = delta
        if len(changed) != 17:
            raise SystemExit(f"{locale}: expected 17 PD1 records, found {len(changed)}")
        desk = airlock.with_name("part-desk.json")
        if desk.exists():
            raise SystemExit(f"{desk}: already exists")
        document = {
            "schema": "fcmo-curated-locale-part-v1", "locale": locale,
            "canonical_locale": "en", "generated_from": "FCMO Publication Desk PD1",
            "canonical_source_sha256": before["canonical_source_sha256"],
            "records": changed,
            "provenance": {rid: {"origin": "publication-desk", "at": AT,
                                 "model": "gpt-5.6-sol", "human_reviewed": False,
                                 "network_translation": False} for rid in changed},
        }
        desk.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        airlock.write_bytes(original)
        print(f"{locale}: moved {len(changed)} exact PD1 field sets; restored {airlock}")


if __name__ == "__main__":
    main()
