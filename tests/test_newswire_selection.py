"""Run the actual selection shell against local Git history; no network or secrets."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


class SnapshotSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.source = self.work / "source"
        self.source.mkdir()
        self.git = shutil.which("git")
        self.run_git("init", "-q", "-b", "main")
        self.run_git("config", "user.name", "Fixture")
        self.run_git("config", "user.email", "fixture@example.invalid")
        (self.source / "tools").mkdir()
        (self.source / "tools/publication_seal.py").write_text("print('SEAL_OK')\n")
        (self.source / "tools/validate_integrity_ratchet.py").write_text("pass\n")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "Sealed fixture")
        self.ready = self.run_git("rev-parse", "HEAD").stdout.strip()
        (self.source / "state").mkdir()
        (self.source / "state/PUBLICATION_READY.json").write_text(json.dumps({
            "schema": "arb-publication-ready-v1", "state": "READY",
            "policy": "immutable-sealed-snapshot", "source_commit": self.ready,
        }))
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "Checkpoint fixture")

    def run_git(self, *args):
        return subprocess.run([self.git, "-C", str(self.source), *args],
                              check=True, text=True, capture_output=True)

    def select(self, *, clone_failures=0, fetch_failures=0, fetch_completed_failure=False, drill=""):
        runner = self.work / "runner"
        runner.mkdir()
        codes = runner / "codes"
        codes.mkdir()
        bin_dir = self.work / "bin"
        bin_dir.mkdir()
        (bin_dir / "python").symlink_to(sys.executable)
        # Only transport is replaced. Clone/fetch/checkout/lineage use real Git.
        shim = '''#!/usr/bin/python3
import os, pathlib, subprocess, sys
args = sys.argv[1:]
for action in ('clone', 'fetch'):
    if action not in args:
        continue
    counter = pathlib.Path(os.environ['RUNNER_TEMP']) / (action + '-attempts')
    count = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(count))
    if count <= int(os.environ[action.upper() + '_FAILURES']):
        if action == 'clone':
            pathlib.Path(args[-1]).mkdir(exist_ok=True)
            (pathlib.Path(args[-1]) / 'partial').touch()
        print('PRIVATE-DIAGNOSTIC-CANARY', file=sys.stderr)
        sys.exit(128)
    if action == 'clone':
        args[-2] = os.environ['FIXTURE_SOURCE']
    break
rc = subprocess.run([os.environ['REAL_GIT'], *args]).returncode
if 'fetch' in args and count == 1 and os.environ['FETCH_COMPLETED_FAILURE'] == '1' and rc == 0:
    sys.exit(128)
sys.exit(rc)
'''
        (bin_dir / "git").write_text(shim)
        (bin_dir / "git").chmod(0o755)
        # Avoid backoff delays in the fixture only.
        (bin_dir / "sleep").write_text("#!/bin/sh\nexit 0\n")
        (bin_dir / "sleep").chmod(0o755)
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/newswire-bridge.yml").read_text()
        step = workflow.split("- name: Select freshest sealed immutable ARB snapshot", 1)[1].split("- name:", 1)[0]
        script = textwrap.dedent(step.split("run: |\n", 1)[1])
        env = {"PATH": str(bin_dir) + os.pathsep + os.defpath, "HOME": str(self.work),
               "RUNNER_TEMP": str(runner), "CODES": str(codes), "APP_TOKEN": "synthetic",
               "FCMO_DRILL": drill, "REAL_GIT": self.git, "FIXTURE_SOURCE": self.source.as_uri(),
               "CLONE_FAILURES": str(clone_failures), "FETCH_FAILURES": str(fetch_failures),
               "FETCH_COMPLETED_FAILURE": str(int(fetch_completed_failure))}
        proc = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script],
                              cwd=self.work, env=env, capture_output=True, text=True, timeout=30)
        self.assertNotIn("PRIVATE-DIAGNOSTIC-CANARY", proc.stdout + proc.stderr)
        self.assertNotIn(self.ready, proc.stdout + proc.stderr)
        return proc, runner, codes

    def test_partial_clone_is_retried_then_selects_exact_main(self):
        proc, runner, codes = self.select(clone_failures=2)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((runner / "clone-attempts").read_text(), "3")
        self.assertEqual((codes / "source_mode").read_text().strip(), "MAIN")
        self.assertEqual((runner / "fcmo-newswire-private-source.sha").read_text().strip(),
                         self.run_git("rev-parse", "HEAD").stdout.strip())
        self.assertFalse((codes / "transport_error").exists())

    def test_history_fetch_retries_and_preserves_sealed_checkpoint_lineage(self):
        proc, runner, codes = self.select(fetch_failures=1, drill="force_checkpoint")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((runner / "fetch-attempts").read_text(), "2")
        self.assertEqual((codes / "source_mode").read_text().strip(), "CHECKPOINT")
        self.assertEqual((runner / "fcmo-newswire-private-source.sha").read_text().strip(), self.ready)

    def test_permanent_clone_failure_is_bounded_and_reports_only_safe_phase(self):
        proc, runner, codes = self.select(clone_failures=99)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual((runner / "clone-attempts").read_text(), "3")
        self.assertEqual((codes / "transport_error").read_text().strip(), "CLONE_FAILED")
        self.assertIn("selection_failure=CLONE_FAILED", proc.stdout)
        self.assertFalse((runner / "fcmo-newswire-private-source.sha").exists())

    def test_permanent_fetch_failure_is_bounded_and_distinguished_from_clone(self):
        proc, runner, codes = self.select(fetch_failures=99)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual((runner / "fetch-attempts").read_text(), "3")
        self.assertEqual((codes / "transport_error").read_text().strip(), "HISTORY_FETCH_FAILED")
        self.assertIn("selection_failure=HISTORY_FETCH_FAILED", proc.stdout)
        self.assertFalse((runner / "fcmo-newswire-private-source.sha").exists())

    def test_retry_after_history_was_unshallowed_does_not_unshallow_twice(self):
        proc, runner, codes = self.select(fetch_completed_failure=True, drill="force_checkpoint")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((runner / "fetch-attempts").read_text(), "2")
        self.assertEqual((codes / "source_mode").read_text().strip(), "CHECKPOINT")
        self.assertEqual((runner / "fcmo-newswire-private-source.sha").read_text().strip(), self.ready)

    def test_missing_checkpoint_stays_closed_with_a_safe_diagnostic(self):
        checkpoint = self.source / "state/PUBLICATION_READY.json"
        doc = json.loads(checkpoint.read_text())
        doc["source_commit"] = "a" * 40
        checkpoint.write_text(json.dumps(doc))
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "Missing checkpoint fixture")
        proc, runner, codes = self.select(drill="force_checkpoint")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual((codes / "transport_error").read_text().strip(), "CHECKPOINT_MISSING")
        self.assertIn("selection_failure=CHECKPOINT_MISSING", proc.stdout)
        self.assertNotIn("a" * 40, proc.stdout + proc.stderr)
        self.assertFalse((runner / "fcmo-newswire-private-source.sha").exists())


if __name__ == "__main__":
    unittest.main()
