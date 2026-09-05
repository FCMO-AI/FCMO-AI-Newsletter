#!/usr/bin/env python3
"""Verify the ingest generator inside the composed autonomous-newsroom pipeline.

`verificar_generador.py` is intentionally a strong ingest oracle: it expects the
canonical release tree to be exactly what `ingest_corpus.py` owns. Since the
newsroom bootstrap, however, `release-src/` is a *composed* tree. After ingest,
two later stages deliberately add or rewrite publication state:

- `public_research_desk.py` owns `data/public-research/` receipts;
- `visual_desk.py` enriches `data/media.json`.

Comparing those downstream products byte-for-byte with bare ingest output is a
layer error, not extra rigor. This adapter keeps the original oracle intact and
adds an explicit composition contract instead of weakening it:

1. reproduce the ingest-owned tree from the frozen corpus;
2. require every ingest-owned path except the explicitly rewritten media ledger
   to match the current release byte-for-byte;
3. allow only the explicit public-research subtree as an extra release-src lane;
4. verify media and research receipt identity/coverage semantically;
5. run the original strong ingest oracle against a temporary repository whose
   release-src is the reproduced ingest substrate.

Thus the generator still has to be idempotent, grow stories/editions and preserve
old surfaces; the newsroom layers merely stop masquerading as generator output.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "_fixtures" / "corpus-2026-09-01"
RELEASE = ROOT / "release-src"
GENERATOR = ROOT / "tools" / "ingest_corpus.py"
LEGACY_ORACLE = Path("tests/oraculos/verificar_generador.py")

# Downstream newsroom ownership. Keep this list deliberately tiny: adding another
# exception requires an explicit architecture decision instead of silently making
# the fixed-point test less observant.
DOWNSTREAM_REWRITTEN = {"data/media.json"}
DOWNSTREAM_EXTRA_PREFIXES = ("data/public-research/",)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def fail(message: str) -> int:
    print(f"el contrato compuesto del generador no cumple: {message}", file=sys.stderr)
    return 1


def canonical_ids(root: Path) -> set[str]:
    brief_dir = root / "data" / "briefs"
    return {path.stem for path in brief_dir.glob("FCMO-*.json")}


def verify_downstream_coverage(release: Path, ids: set[str]) -> list[str]:
    errors: list[str] = []

    media_path = release / "data" / "media.json"
    try:
        media = json.loads(media_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"data/media.json no es JSON legible: {exc}"]
    media_ids = [row.get("id") for row in media if isinstance(row, dict)] if isinstance(media, list) else []
    if len(media_ids) != len(set(media_ids)):
        errors.append("data/media.json tiene IDs duplicados")
    if set(media_ids) != ids:
        errors.append(
            "data/media.json no cubre exactamente el corpus: "
            f"faltan={sorted(ids - set(media_ids))[:8]} sobran={sorted(set(media_ids) - ids)[:8]}"
        )

    research_dir = release / "data" / "public-research"
    receipt_paths = sorted(research_dir.glob("FCMO-*.json")) if research_dir.is_dir() else []
    receipt_ids = {path.stem for path in receipt_paths}
    if receipt_ids != ids:
        errors.append(
            "data/public-research no cubre exactamente el corpus: "
            f"faltan={sorted(ids - receipt_ids)[:8]} sobran={sorted(receipt_ids - ids)[:8]}"
        )
    for path in receipt_paths:
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path.relative_to(release)} no es JSON legible: {exc}")
            continue
        if receipt.get("schema") != "fcmo-public-research-receipt-v1":
            errors.append(f"{path.relative_to(release)} tiene schema inesperado")
        if receipt.get("id") != path.stem:
            errors.append(f"{path.relative_to(release)} declara id={receipt.get('id')!r}")
        if not receipt.get("canonical_signature"):
            errors.append(f"{path.relative_to(release)} no conserva canonical_signature")
        if receipt.get("trust_boundary") != "sanitized public brief + public Internet only":
            errors.append(f"{path.relative_to(release)} perdio el trust boundary clean-room")
    return errors


def main() -> int:
    for required in (CORPUS, RELEASE, GENERATOR, ROOT / LEGACY_ORACLE):
        if not required.exists():
            return fail(f"falta {required.relative_to(ROOT)}")

    with tempfile.TemporaryDirectory(prefix="fcmo-newsroom-gen-") as temp:
        tmp = Path(temp)
        ingest = tmp / "ingest"
        generated = run(str(GENERATOR), "--corpus", str(CORPUS), "--out", str(ingest))
        if generated.returncode:
            return fail(
                "ingest_corpus.py no pudo reproducir el sustrato: "
                + (generated.stderr or generated.stdout or "").strip()[-1200:]
            )

        current_tree = tree(RELEASE)
        ingest_tree = tree(ingest)

        missing = sorted(path for path in ingest_tree if path not in current_tree)
        differing = sorted(
            path
            for path, sha in ingest_tree.items()
            if path in current_tree
            and path not in DOWNSTREAM_REWRITTEN
            and current_tree[path] != sha
        )
        unexpected_extra = sorted(
            path
            for path in current_tree
            if path not in ingest_tree
            and not any(path.startswith(prefix) for prefix in DOWNSTREAM_EXTRA_PREFIXES)
        )
        if missing or differing or unexpected_extra:
            return fail(
                "drift entre sustrato de ingesta y release compuesto; "
                f"faltan={missing[:8]} difieren={differing[:8]} extras_no_declarados={unexpected_extra[:8]}"
            )

        ids = canonical_ids(ingest)
        coverage_errors = verify_downstream_coverage(RELEASE, ids)
        if coverage_errors:
            for error in coverage_errors:
                print(f"  - {error}", file=sys.stderr)
            return fail(f"{len(coverage_errors)} errores en capas downstream")

        # Run the original ingest oracle without editing it. Its canonical BASE is
        # replaced only inside this disposable checkout by the reproduced ingest
        # substrate. The production repository remains untouched.
        sandbox = tmp / "repo"
        shutil.copytree(
            ROOT,
            sandbox,
            ignore=shutil.ignore_patterns(
                ".git", "publish", "regression", "__pycache__", "_audit"
            ),
        )
        shutil.rmtree(sandbox / "release-src")
        shutil.copytree(ingest, sandbox / "release-src")
        legacy = run(str(LEGACY_ORACLE), cwd=sandbox)
        if legacy.returncode:
            print(legacy.stdout, file=sys.stderr)
            print(legacy.stderr, file=sys.stderr)
            return fail("el oraculo fuerte de ingesta fallo sobre su propio sustrato")

    print(
        "generador compuesto OK: sustrato de ingesta reproducible; "
        "public-research/media separados por ownership; oraculo fuerte de ingesta verde"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
