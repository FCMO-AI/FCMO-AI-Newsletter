"""Reader-facing enum coverage of the UI catalogs.

Two uses, deliberately separated:

* ``tests/test_localization_completeness.py`` checks the catalogs against a FROZEN
  snapshot (``tests/fixtures/ui_enum_snapshot.json``) so the publication gate never
  depends on which values the hourly corpus happened to bring in.
* ``python3 tools/ui_label_coverage.py`` checks the LIVE corpus and only warns
  (exit 0, GitHub ``::warning::`` lines) unless ``--strict`` is given. A new value
  renders with the generic label (``labels.<group>.other``) until a label is added.
  ``--freeze`` rewrites the snapshot from the live corpus.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("en", "es-419", "zh-Hans")
GROUPS = ("desk", "development_type", "confidence", "evidence_class", "importance_tier", "record_status",
          "claim_label", "gap_kind", "gap_state", "region", "source_language", "story_type",
          "media_mode", "rights_state")
SNAPSHOT = ROOT / "tests/fixtures/ui_enum_snapshot.json"


def observed_live(root: Path = ROOT) -> dict[str, set[str]]:
    observed: dict[str, set[str]] = {group: set() for group in GROUPS}
    for line in (root / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        observed["desk"].update(r.get("desks") or [])
        observed["desk"].add(r.get("primary_desk"))
        observed["development_type"].add(r.get("development_type"))
        observed["confidence"].add(r.get("confidence"))
        observed["evidence_class"].add(r.get("evidence_class"))
        observed["importance_tier"].add(r.get("importance_tier"))
        observed["record_status"].add(r.get("status"))
        observed["region"].update(r.get("regions") or [])
        observed["source_language"].update(r.get("source_languages") or [])
        for claim in r.get("claims") or []:
            observed["claim_label"].add(claim.get("label"))
        for gap in r.get("evidence_gaps") or []:
            observed["gap_kind"].add(gap.get("kind"))
            observed["gap_state"].add(gap.get("state"))
    for story in json.loads((root / "site/data/stories.json").read_text(encoding="utf-8")):
        observed["story_type"].add(story.get("story_type"))
        observed["confidence"].add((story.get("news_value") or {}).get("confidence"))
        observed["evidence_class"].add((story.get("news_value") or {}).get("evidence"))
        media = story.get("media") or {}
        observed["media_mode"].add(media.get("mode"))
        observed["rights_state"].add(media.get("rights_state"))
    return {group: {v for v in values if isinstance(v, str) and v} for group, values in observed.items()}


def contract_enums(root: Path = ROOT) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for name in ("record.v3", "stories.v2", "newsroom-status.v2"):
        schema = json.loads((root / f"contracts/{name}.schema.json").read_text(encoding="utf-8"))
        enums: set[str] = set()

        def walk(node):
            if isinstance(node, dict):
                if isinstance(node.get("enum"), list):
                    enums.update(v for v in node["enum"] if isinstance(v, str))
                for item in node.values():
                    walk(item)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(schema)
        out[f"contract:{name}"] = enums
    return out


def load_catalogs(root: Path = ROOT) -> dict[str, dict]:
    return {loc: json.loads((root / f"i18n/ui/{loc}.json").read_text(encoding="utf-8")) for loc in LOCALES}


def missing_labels(catalogs: dict[str, dict], observed: dict[str, set[str]]) -> list[str]:
    missing = []
    for locale in LOCALES:
        labels = catalogs[locale]["labels"]
        everything = set().union(*(set(group) for group in labels.values()))
        for group, codes in observed.items():
            for code in sorted(c for c in codes if c):
                if group.startswith("contract:"):
                    if code not in everything:
                        missing.append(f"{locale}: {group} enum {code} has no label")
                elif code not in labels.get(group, {}):
                    missing.append(f"{locale}: labels.{group}.{code} missing")
    return missing


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, set[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {group: set(values) for group, values in data["observed"].items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 when the live corpus has unlabeled values")
    parser.add_argument("--freeze", action="store_true", help="rewrite the frozen snapshot from the live corpus")
    args = parser.parse_args(argv)
    observed = observed_live()
    if args.freeze:
        SNAPSHOT.write_text(json.dumps({
            "about": "Frozen reader-facing enum values the publication gate requires labels for. "
                     "Regenerate with: python3 tools/ui_label_coverage.py --freeze",
            "observed": {group: sorted(values) for group, values in observed.items()},
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"snapshot written: {SNAPSHOT}")
        return 0
    missing = missing_labels(load_catalogs(), observed)
    for line in missing:
        print(f"::warning title=UI label missing (renders generic)::{line}")
    print(f"live-corpus label coverage: {len(missing)} missing"
          + ("" if not missing else " (generic label shown to readers until added)"))
    return 1 if (missing and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
