from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/pages.yml"


class PagesWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_candidate_order_is_build_gates_browser_deploy_live_verify(self):
        positions = [
            self.text.index("python tools/paper/build.py"),
            self.text.index("python tools/gates/run_all.py publish"),
            self.text.index("python tests/oraculos/verificar_paper.py publish"),
            self.text.index("uses: actions/upload-pages-artifact@v4"),
            self.text.index("uses: actions/deploy-pages@v4"),
            self.text.index("python tools/verify_live_front_page.py"),
            self.text.index("git tag -f lkg"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_failed_gate_cannot_reach_deploy(self):
        self.assertIn("needs: build", self.text)
        self.assertNotIn("continue-on-error: true", self.text)
        build = self.text[self.text.index("  build:"):self.text.index("  deploy:")]
        self.assertIn("Run every deterministic publication gate before deploy", build)
        self.assertIn("Upload only the fully gated candidate", build)

    def test_lkg_is_durable_and_moves_only_after_live_verification(self):
        self.assertIn("refs/tags/lkg^{commit}", self.text)
        self.assertIn("needs: live-verify", self.text)
        promote = self.text[self.text.index("  promote-lkg:"):self.text.index("  rollback-build:")]
        self.assertIn("git push --force origin refs/tags/lkg", promote)
        self.assertNotIn("upload-pages-artifact", promote)

    def test_failed_live_verify_runs_rollback_from_lkg(self):
        rollback = self.text[self.text.index("  rollback-build:"):]
        self.assertIn("needs.live-verify.result == 'failure'", rollback)
        self.assertRegex(rollback, r"ref: lkg")
        self.assertIn("Redeploy LKG", rollback)
        self.assertIn("Prove the public origin is serving LKG again", rollback)
        self.assertIn("if test -f lkg-source/tools/paper/build.py", rollback)

    def test_manual_rollback_is_one_dispatch_input(self):
        dispatch = self.text[self.text.index("workflow_dispatch:"):self.text.index("permissions:")]
        self.assertIn("operation:", dispatch)
        self.assertIn("options: [deploy, rollback]", dispatch)
        self.assertIn("inputs.operation == 'rollback'", self.text)

    def test_cdn_cache_is_polled_before_rollback(self):
        self.assertIn("--timeout-seconds 900", self.text)
        self.assertIn("--poll-seconds 15", self.text)
        source = (ROOT / "tools/verify_live_front_page.py").read_text(encoding="utf-8")
        self.assertIn("fcmo_verify", source)
        self.assertIn("candidate never reached the origin", source)

    def test_drill_inputs_cannot_arrive_from_push_or_schedule(self):
        # There are no production-breaking drill inputs on non-manual events.
        self.assertNotIn("break_identity_after_deploy", self.text)
        self.assertNotIn("inject_english_leak", self.text)


if __name__ == "__main__": unittest.main()
