#!/usr/bin/env python3
"""Prove generator behavior without treating committed release output as input.

The publication desk can update ``corpus/`` before the newsroom composes
``release-src/``. CI must therefore test the generator against a baseline it
creates from the same checkout at test time, not require those independently
updated artifacts to be byte-for-byte synchronized at merge time.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT_CORPUS = ROOT / "corpus"
GENERATOR = ROOT / "tools" / "ingest_corpus.py"
LEGACY_ORACLE = Path("tests/oraculos/verificar_generador.py")
TEST_CORPUS = Path("_fixtures/corpus-2026-09-01")


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
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


def main() -> int:
    for required, label in (
        (CURRENT_CORPUS, "corpus sanitizado actual"),
        (GENERATOR, "generador"),
        (ROOT / LEGACY_ORACLE, "oraculo de crecimiento/idempotencia"),
    ):
        if not required.exists():
            return fail(f"falta {label}: {required.relative_to(ROOT)}")

    with tempfile.TemporaryDirectory(prefix="fcmo-newsroom-gen-") as temporary:
        sandbox = Path(temporary) / "repo"
        shutil.copytree(
            ROOT,
            sandbox,
            ignore=shutil.ignore_patterns(
                ".git", "publish", "regression", "__pycache__", "_audit", ".pytest_cache"
            ),
        )

        # Build the oracle's release baseline from this checkout's corpus. The
        # committed release-src may legitimately lag while main is receiving
        # the next edition, so it must not participate in this comparison.
        fixture_corpus = sandbox / TEST_CORPUS
        shutil.rmtree(fixture_corpus, ignore_errors=True)
        shutil.copytree(CURRENT_CORPUS, fixture_corpus)
        shutil.rmtree(sandbox / "release-src", ignore_errors=True)
        generated = run(
            "tools/ingest_corpus.py",
            "--corpus",
            TEST_CORPUS.as_posix(),
            "--out",
            "release-src",
            cwd=sandbox,
        )
        if generated.returncode:
            return fail(
                "no se pudo generar el baseline desde el corpus de este checkout: "
                + (generated.stderr or generated.stdout or "").strip()[-1200:]
            )

        growth = run(LEGACY_ORACLE.as_posix(), cwd=sandbox)
        if growth.returncode:
            print(growth.stdout, file=sys.stderr)
            print(growth.stderr, file=sys.stderr)
            return fail("el oraculo de crecimiento/idempotencia fallo con su baseline generado")

    print(
        "generador compuesto OK: baseline generado desde el corpus del checkout; "
        "crecimiento de historias/ediciones e idempotencia comprobados"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
