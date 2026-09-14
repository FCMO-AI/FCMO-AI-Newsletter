#!/usr/bin/env python3
"""Verify ingest ownership inside the current autonomous-newsroom pipeline.

Two deliberately separate checks live here:

1. production truth: current ``release-src`` must be explainable by the current
   sanitized ``corpus/`` plus a small, explicit set of downstream-owned lanes;
2. generator behavior: the older synthetic growth/idempotence oracle runs in a
   disposable checkout whose baseline is generated from its own frozen fixture.

Keeping those worlds separate matters. A historical fixture is excellent for a
stable counterfactual growth test, but it must never be compared byte-for-byte
with today's 100+ Story production tree.
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
CURRENT_CORPUS = ROOT / "corpus"
FIXTURE_CORPUS = ROOT / "_fixtures" / "corpus-2026-09-01"
RELEASE = ROOT / "release-src"
GENERATOR = ROOT / "tools" / "ingest_corpus.py"
LEGACY_ORACLE = Path("tests/oraculos/verificar_generador.py")

DOWNSTREAM_REWRITTEN = {"data/media.json", "agent.json", "data/site-manifest.json"}
DOWNSTREAM_REWRITTEN_PREFIXES = ("data/briefs/",)
DOWNSTREAM_EXTRA_EXACT = {"data/relationships.jsonl"}
DOWNSTREAM_EXTRA_PREFIXES = ("data/public-research/",)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*")) if p.is_file()}


def downstream_rewritten(path: str) -> bool:
    return path in DOWNSTREAM_REWRITTEN or any(path.startswith(prefix) for prefix in DOWNSTREAM_REWRITTEN_PREFIXES)


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def fail(message: str) -> int:
    print(f"el contrato compuesto del generador no cumple: {message}", file=sys.stderr)
    return 1


def canonical_ids(root: Path) -> set[str]:
    return {p.stem for p in (root / "data" / "briefs").glob("FCMO-*.json")}


def verify_downstream_coverage(release: Path, ids: set[str]) -> list[str]:
    errors: list[str] = []
    brief_ids = {p.stem for p in (release / "data" / "briefs").glob("FCMO-*.json")}
    if brief_ids != ids:
        errors.append(f"data/briefs no cubre exactamente el corpus: faltan={sorted(ids-brief_ids)[:8]} sobran={sorted(brief_ids-ids)[:8]}")

    media_path = release / "data" / "media.json"
    try:
        media = json.loads(media_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return errors + [f"data/media.json no es JSON legible: {exc}"]
    media_ids = [row.get("id") for row in media if isinstance(row, dict)] if isinstance(media, list) else []
    if len(media_ids) != len(set(media_ids)):
        errors.append("data/media.json tiene IDs duplicados")
    if set(media_ids) != ids:
        errors.append(f"data/media.json no cubre exactamente el corpus: faltan={sorted(ids-set(media_ids))[:8]} sobran={sorted(set(media_ids)-ids)[:8]}")

    research_dir = release / "data" / "public-research"
    receipt_paths = sorted(research_dir.glob("FCMO-*.json")) if research_dir.is_dir() else []
    receipt_ids = {p.stem for p in receipt_paths}
    if receipt_ids != ids:
        errors.append(f"data/public-research no cubre exactamente el corpus: faltan={sorted(ids-receipt_ids)[:8]} sobran={sorted(receipt_ids-ids)[:8]}")
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
    for required in (CURRENT_CORPUS, FIXTURE_CORPUS, RELEASE, GENERATOR, ROOT / LEGACY_ORACLE):
        if not required.exists():
            return fail(f"falta {required.relative_to(ROOT)}")

    with tempfile.TemporaryDirectory(prefix="fcmo-newsroom-gen-") as temp:
        tmp = Path(temp)

        # A. Current production provenance/ownership.
        ingest = tmp / "current-ingest"
        generated = run(str(GENERATOR), "--corpus", str(CURRENT_CORPUS), "--out", str(ingest))
        if generated.returncode:
            return fail("ingest_corpus.py no pudo reproducir el corpus actual: " + (generated.stderr or generated.stdout or "").strip()[-1200:])

        current_tree, ingest_tree = tree(RELEASE), tree(ingest)
        missing = sorted(path for path in ingest_tree if path not in current_tree)
        differing = sorted(path for path, sha in ingest_tree.items() if path in current_tree and not downstream_rewritten(path) and current_tree[path] != sha)
        unexpected_extra = sorted(
            path for path in current_tree
            if path not in ingest_tree
            and path not in DOWNSTREAM_EXTRA_EXACT
            and not any(path.startswith(prefix) for prefix in DOWNSTREAM_EXTRA_PREFIXES)
        )
        if missing or differing or unexpected_extra:
            return fail(f"drift entre corpus actual y release compuesto; faltan={missing[:8]} difieren={differing[:8]} extras_no_declarados={unexpected_extra[:8]}")

        ids = canonical_ids(ingest)
        coverage_errors = verify_downstream_coverage(RELEASE, ids)
        if coverage_errors:
            for error in coverage_errors:
                print(f"  - {error}", file=sys.stderr)
            return fail(f"{len(coverage_errors)} errores en capas downstream")

        # B. Stable synthetic growth/idempotence proof in its own disposable world.
        fixture_base = tmp / "fixture-base"
        seeded = run(str(GENERATOR), "--corpus", str(FIXTURE_CORPUS), "--out", str(fixture_base))
        if seeded.returncode:
            return fail("no se pudo crear baseline del fixture historico: " + (seeded.stderr or seeded.stdout or "").strip()[-1200:])

        sandbox = tmp / "legacy-repo"
        shutil.copytree(ROOT, sandbox, ignore=shutil.ignore_patterns(".git", "publish", "regression", "__pycache__", "_audit", ".pytest_cache"))
        shutil.rmtree(sandbox / "release-src", ignore_errors=True)
        shutil.copytree(fixture_base, sandbox / "release-src")
        legacy = run(str(LEGACY_ORACLE), cwd=sandbox)
        if legacy.returncode:
            print(legacy.stdout, file=sys.stderr)
            print(legacy.stderr, file=sys.stderr)
            return fail("el oraculo fuerte de crecimiento/idempotencia fallo en su sandbox historico")

    print("generador compuesto OK: produccion ligada al corpus actual; ownership downstream explicito; crecimiento/idempotencia sinteticos aislados y verdes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
