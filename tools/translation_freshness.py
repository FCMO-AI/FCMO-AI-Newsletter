#!/usr/bin/env python3
"""Invalidate and record per-story translation source digests.

Global corpus hashes prove pack identity but cannot tell which existing story
changed. This tool gives every canonical story a prose digest. A changed
digest removes that story's locale overlay before translation, forcing the
normal translator to regenerate it instead of silently reusing stale prose.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_RE = re.compile(
    r'<script\s+id=["\']fcmo-data["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.S | re.I,
)
PROSE_STRINGS = ("title", "summary", "why_it_matters", "why", "importance_rationale")
PROSE_LISTS = ("limitations", "contradictory_evidence", "engineering_implications", "policy_implications", "research_implications")
PROSE_OBJECT_LISTS = {"claims": ("text",), "evidence_gaps": ("description",), "relationships": ("summary",)}
PROSE_DICTS = ("technical",)


def canonical(site: Path) -> dict[str, dict[str, Any]]:
    text = (site / "index.html").read_text(encoding="utf-8")
    match = SCRIPT_RE.search(text)
    if not match:
        raise SystemExit("translation freshness: canonical fcmo-data missing")
    rows = json.loads(match.group(1)).get("records")
    if not isinstance(rows, list):
        raise SystemExit("translation freshness: canonical records missing")
    return {row["id"]: row for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str)}


def prose_overlay(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in PROSE_STRINGS:
        if key in record:
            out[key] = record[key]
    for key in PROSE_LISTS:
        if key in record:
            out[key] = record[key]
    for key, fields in PROSE_OBJECT_LISTS.items():
        if key in record:
            out[key] = [
                {field: item[field] for field in fields if isinstance(item, dict) and field in item}
                for item in record[key]
            ]
    for key in PROSE_DICTS:
        if key in record and isinstance(record[key], dict):
            out[key] = record[key]
    return out


def digest(record: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(prose_overlay(record), ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def atomic(path: Path, doc: dict[str, Any], compact: bool) -> None:
    text = (
        json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"
        if compact
        else json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent,
        prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    os.replace(tmp, path)


def locale_parts(i18n: Path, locale: str) -> list[Path]:
    return sorted((i18n / locale).glob("part-*.json"))


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": "fcmo-translation-source-digests-v1", "records": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "fcmo-translation-source-digests-v1":
        raise SystemExit("translation freshness: unsupported manifest schema")
    return value


def invalidate(site: Path, i18n: Path, manifest_path: Path) -> int:
    records = canonical(site)
    current = {rid: digest(row) for rid, row in records.items()}
    manifest = load_manifest(manifest_path)
    previous = manifest.get("records") or {}
    # Footnote: absence of a per-record manifest is not evidence of freshness.
    # The first v1 run intentionally re-translates the corpus once to establish
    # a trustworthy baseline rather than grandfathering unknown semantic state.
    stale = {rid for rid, value in current.items() if previous.get(rid) != value}
    stale.update(set(previous) - set(current))
    touched = 0
    for locale in ("es-419", "zh-Hans"):
        for path in locale_parts(i18n, locale):
            original = path.read_text(encoding="utf-8")
            doc = json.loads(original)
            rows = doc.get("records")
            if not isinstance(rows, dict):
                raise SystemExit(f"{path}: records object missing")
            new = {rid: value for rid, value in rows.items() if rid not in stale and rid in records}
            if new != rows:
                doc["records"] = new
                atomic(path, doc, compact="\n" not in original.rstrip("\n"))
                touched += 1
    print(f"translation freshness invalidation OK; stale={len(stale)}; touched_parts={touched}")
    return 0


def record(site: Path, i18n: Path, manifest_path: Path) -> int:
    records = canonical(site)
    expected = set(records)
    for locale in ("es-419", "zh-Hans"):
        ids: set[str] = set()
        for path in locale_parts(i18n, locale):
            doc = json.loads(path.read_text(encoding="utf-8"))
            ids.update((doc.get("records") or {}).keys())
        if ids != expected:
            missing = sorted(expected - ids)
            extra = sorted(ids - expected)
            raise SystemExit(f"translation freshness record refused for {locale}: missing={missing} extra={extra}")
    obj = {
        "schema": "fcmo-translation-source-digests-v1",
        "records": {rid: digest(row) for rid, row in sorted(records.items())},
    }
    atomic(manifest_path, obj, compact=False)
    print(f"translation freshness manifest recorded; stories={len(records)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--manifest", type=Path, default=Path("site/data/i18n/source-digests.json"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--invalidate", action="store_true")
    mode.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    return invalidate(args.site, args.i18n_dir, args.manifest) if args.invalidate else record(args.site, args.i18n_dir, args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
