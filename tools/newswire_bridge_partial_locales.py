#!/usr/bin/env python3
"""Production Airlock transport with truthful partial native-locale coverage.

The original ``newswire_bridge.py`` remains the strict all-locales-parity verifier.
Production freshness uses the same privacy/content-addressing/path checks, but a new
English Story may cross before its ES/ZH prose is authored. Locale deltas must remain
well-formed, source-authored, symmetric between ES/ZH, and subsets of the public
corpus. Missing translations are handled downstream as explicit pending pages.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from tools import newswire_bridge as strict


def _public_ids(release: Path) -> set[str]:
    errors: list[str] = []
    ids = strict._canonical_ids(release / "data" / "developments.jsonl", errors)
    if errors:
        raise ValueError("public corpus identity validation failed: " + "; ".join(errors))
    return ids


def _locale_delta_ids(release: Path, locale: str) -> set[str]:
    path = release / "data" / "locales" / locale / "records.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc.get("records") if isinstance(doc, dict) else None
    if not isinstance(rows, dict):
        raise ValueError(f"{locale}: locale records missing")
    return set(rows)


def _synthetic_coverage_baseline(release: Path) -> Path:
    """Create a verifier-only baseline proving coverage without inventing prose.

    ``newswire_bridge.verify_release`` validates public paths, digests, privacy,
    schemas and locale record shapes; its only production-incompatible rule is that
    baseline+delta cover every English ID. Give that one check a temporary ID-only
    baseline. No synthetic overlay is staged or persisted, and we independently prove
    the real incoming locale sets are symmetric subsets of the corpus below.
    """
    ids = sorted(_public_ids(release))
    root = Path(tempfile.mkdtemp(prefix="fcmo-locale-coverage-proof-"))
    for locale in strict.LOCALES:
        folder = root / locale
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "part-coverage-proof.json").write_text(
            json.dumps(
                {
                    "schema": strict.CURATED_PART_SCHEMA,
                    "locale": locale,
                    "canonical_locale": "en",
                    "records": {rid: {} for rid in ids},
                },
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
    return root


def verify_release(release: Path) -> dict[str, Any]:
    release = release.resolve()
    proof = _synthetic_coverage_baseline(release)
    try:
        receipt = strict.verify_release(release, proof)
    finally:
        shutil.rmtree(proof, ignore_errors=True)

    ids = _public_ids(release)
    locale_sets = {locale: _locale_delta_ids(release, locale) for locale in strict.LOCALES}
    for locale, localized in locale_sets.items():
        extra = localized - ids
        if extra:
            raise ValueError(f"{locale}: locale delta contains IDs outside public corpus")
    if locale_sets[strict.LOCALES[0]] != locale_sets[strict.LOCALES[1]]:
        raise ValueError("native locale delta ID sets differ between es-419 and zh-Hans")

    translated = len(locale_sets[strict.LOCALES[0]])
    pending = len(ids - locale_sets[strict.LOCALES[0]])
    print(
        f"partial-locale Airlock OK: stories={len(ids)} translated_delta={translated} "
        f"pending={pending}"
    )
    return receipt


def stage_release(release: Path, corpus: Path) -> dict[str, Any]:
    release = release.resolve()
    corpus = corpus.resolve()
    receipt = verify_release(release)
    corpus.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{corpus.name}.stage-", dir=corpus.parent))
    backup = corpus.parent / f".{corpus.name}.previous"
    try:
        shutil.rmtree(stage)
        shutil.copytree(release, stage, symlinks=False)
        verify_release(stage)
        if backup.exists():
            shutil.rmtree(backup)
        if corpus.exists():
            corpus.rename(backup)
        stage.rename(corpus)
        verify_release(corpus)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if not corpus.exists() and backup.exists():
            backup.rename(corpus)
        raise
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("verify")
    v.add_argument("release", type=Path)
    s = sub.add_parser("stage")
    s.add_argument("release", type=Path)
    s.add_argument("corpus", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = verify_release(args.release) if args.command == "verify" else stage_release(args.release, args.corpus)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=os.sys.stderr)
        return 1
    print(f"airlock transfer OK: {receipt.get('release_id')} records={receipt.get('record_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
