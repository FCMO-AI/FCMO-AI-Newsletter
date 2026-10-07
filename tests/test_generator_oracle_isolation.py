"""The generator oracle must not depend on yesterday's committed release."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class GeneratorOracleIsolation(unittest.TestCase):
    def test_current_corpus_oracle_runs_without_committed_release_src(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fcmo-generator-oracle-") as temporary:
            sandbox = Path(temporary)
            for name in ("tools", "corpus", "_fixtures"):
                shutil.copytree(ROOT / name, sandbox / name)
            shutil.copytree(ROOT / "tests" / "oraculos", sandbox / "tests" / "oraculos")
            self.assertFalse((sandbox / "release-src").exists())

            result = subprocess.run(
                [sys.executable, "tests/oraculos/verificar_generador_newsroom.py"],
                cwd=sandbox,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            self.assertEqual(
                result.returncode,
                0,
                (result.stdout or "") + "\n" + (result.stderr or ""),
            )


if __name__ == "__main__":
    unittest.main()
