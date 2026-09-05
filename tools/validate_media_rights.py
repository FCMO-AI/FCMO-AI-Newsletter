#!/usr/bin/env python3
"""Fail closed on new story imagery without an explicit reuse basis.

Legacy externally sourced images are frozen in a migration allowlist so this upgrade does
not silently delete the existing visual archive. The allowlist is not an approval
mechanism: new IDs may not be added by the autonomous Visual Desk.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

APPROVED_RIGHTS = {"CC_BY", "CC0", "PUBLIC_DOMAIN", "FIRST_PARTY_REUSE_LICENSE", "FCMO_OWNED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--legacy", type=Path, default=Path("config/media_legacy_allowlist.json"))
    args = parser.parse_args()
    media = json.loads((args.site / "data" / "media.json").read_text(encoding="utf-8"))
    legacy = set(json.loads(args.legacy.read_text(encoding="utf-8")).get("ids") or [])
    errors: list[str] = []
    for item in media:
        identifier = item.get("id", "<missing-id>")
        mode = item.get("mode")
        sourced = item.get("sourced") is True or mode == "real_preferred"
        if mode == "fcmo_generated":
            if item.get("rights_state") != "FCMO_OWNED":
                errors.append(f"{identifier}: generated visual is not marked FCMO_OWNED")
            if not str(item.get("image_url") or "").startswith("assets/story-media/"):
                errors.append(f"{identifier}: generated visual must be a local story-media asset")
            continue
        if not sourced:
            continue
        if identifier in legacy:
            continue
        rights = item.get("rights_state")
        if rights not in APPROVED_RIGHTS:
            errors.append(f"{identifier}: new sourced image lacks approved rights_state")
        if not item.get("credit"):
            errors.append(f"{identifier}: new sourced image lacks credit")
        if rights != "FCMO_OWNED" and not item.get("license_url"):
            errors.append(f"{identifier}: new sourced image lacks license_url")
    if errors:
        print("media rights gate FAILED")
        for error in errors:
            print("-", error)
        return 1
    print(f"media rights gate OK; assets={len(media)}; grandfathered={sum(1 for x in media if x.get('id') in legacy)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
