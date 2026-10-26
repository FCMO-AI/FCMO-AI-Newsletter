"""Exercise the real suppressed workflow step without network or private inputs."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest
from unittest.mock import patch

from tests import test_newswire_bridge as fixtures
from tools import newswire_bridge_partial_locales as partial, wire_status


class BridgeDiagnosticsTests(unittest.TestCase):
    setUp = fixtures.NewswireBridgeTests.setUp
    tearDown = fixtures.NewswireBridgeTests.tearDown
    _write = fixtures.NewswireBridgeTests._write
    _write_safe_release = fixtures.NewswireBridgeTests._write_safe_release
    _restamp = fixtures.NewswireBridgeTests._restamp

    def run_verify_step(self):
        repo = Path(__file__).resolve().parents[1]
        workflow = (repo / ".github/workflows/newswire-bridge.yml").read_text()
        step = workflow.split("- name: Independently verify the airlocked bytes", 1)[1].split("- name:", 1)[0]
        script = textwrap.dedent(step.split("run: |\n", 1)[1])
        work = Path(self.tmp.name)
        codes = work / "codes"
        codes.mkdir()
        summary = work / "summary.md"
        summary.touch()
        bin_dir = work / "bin"
        bin_dir.mkdir()
        (bin_dir / "python").symlink_to(sys.executable)
        env = {"PATH": str(bin_dir) + os.pathsep + os.defpath, "HOME": str(work),
               "RELEASE_DIR": str(self.root), "CODES": str(codes), "GITHUB_STEP_SUMMARY": str(summary)}
        proc = subprocess.run(["bash", "-c", script], cwd=repo, env=env, capture_output=True, text=True)
        return proc, codes, summary.read_text()

    def test_verify_failure_reaches_wire_status_and_summary_without_private_text(self):
        self._write("index.html", "<html>PRIVATE-CANARY: not an ARB-run reproduction</html>")
        self._restamp()
        proc, codes, summary = self.run_verify_step()
        self.assertEqual(proc.returncode, 1)
        code = (codes / "transport_error").read_text().strip()
        self.assertEqual(code, "VERIFY:PRIVATE_MARKER")
        self.assertIsNotNone(wire_status.CODE_RE.fullmatch(code))
        # The same code must survive the production status writer unchanged.
        status_path = codes / "wire-status.json"
        repo = Path(__file__).resolve().parents[1]
        status = subprocess.run([
            sys.executable, str(repo / "tools/wire_status.py"), "write", "--out", str(status_path),
            "--now", "2026-10-26T06:00:00Z", "--transport", "FAIL", "--transport-error", code,
        ], cwd=repo, capture_output=True, text=True)
        self.assertEqual(status.returncode, 0, status.stderr)
        doc = json.loads(status_path.read_text())
        self.assertEqual(doc["transport_error"], code)
        self.assertEqual(wire_status.wire_errors(doc), [])
        self.assertIn(code, summary)
        self.assertIn("rechazada", summary)
        for output in (proc.stdout, proc.stderr, summary, code):
            self.assertNotIn("PRIVATE-CANARY", output)
            self.assertNotIn("ARB-run", output)

    def test_quarantine_integrity_failure_is_visible_without_resealing(self):
        self._write("index.html", "TAMPERED-CANARY")
        original = (self.root / "airlock.json").read_bytes()
        proc, codes, summary = self.run_verify_step()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual((codes / "transport_error").read_text().strip(), "QUARANTINE:INTEGRITY")
        self.assertIn("QUARANTINE:INTEGRITY", summary)
        self.assertNotIn("TAMPERED-CANARY", proc.stdout + proc.stderr + summary)
        self.assertEqual((self.root / "airlock.json").read_bytes(), original)

    def test_workflow_isolates_private_edition_without_a_public_payload_channel(self):
        self._write("editions/2026-10-24.html", "<html>PRIVATE-CANARY: not an ARB-run reproduction</html>")
        self._restamp()
        proc, codes, summary = self.run_verify_step()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse((codes / "transport_error").exists())
        self.assertEqual((codes / "quarantined").read_text(), "")
        self.assertEqual(summary, "")
        self.assertNotIn("PRIVATE-CANARY", proc.stdout + proc.stderr + summary)
        self.assertEqual(json.loads((self.root / "airlock.json").read_text())["record_count"], 1)

    def test_unclassified_exception_never_becomes_a_public_diagnostic(self):
        work = Path(self.tmp.name)
        code, summary = work / "code", work / "summary"
        output = io.StringIO()
        with patch.object(partial, "verify_release", side_effect=ValueError("PRIVATE-CANARY")):
            with contextlib.redirect_stderr(output):
                rc = partial.main(["verify", str(self.root), "--error-code-out", str(code)])
        self.assertEqual(rc, 1)
        self.assertEqual(partial.main(["report", "--code-file", str(code), "--summary", str(summary)]), 0)
        self.assertEqual(code.read_text().strip(), "VERIFY:UNCLASSIFIED")
        self.assertIn("VERIFY:UNCLASSIFIED", summary.read_text())
        self.assertNotIn("PRIVATE-CANARY", output.getvalue() + summary.read_text())

    def test_reporter_rejects_forged_codes_including_well_formed_private_names(self):
        work = Path(self.tmp.name)
        code, summary = work / "code", work / "summary"
        for value in ("VERIFY:PRIVATE_CANARY", "VERIFY:PRIVATE_MARKER\nPRIVATE-CANARY", "X" * 1000,
                      "::warning::PRIVATE-CANARY", "\xff"):
            with self.subTest(value=value):
                code.write_text(value)
                summary.write_text("")
                self.assertEqual(partial.main(["report", "--code-file", str(code), "--summary", str(summary)]), 0)
                self.assertEqual(summary.read_text(), "Verificación del airlock rechazada: `VERIFY:UNCLASSIFIED`.\n")


if __name__ == "__main__":
    unittest.main()
