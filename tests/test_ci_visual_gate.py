"""Contract tests for the all-routes Playwright CI visual gate."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "tests" / "oraculos" / "verificar_ci_visual.py"
sys.path.insert(0, str(ROOT))
from tools.paper.playwright_module import resolve_playwright_module  # noqa: E402


class CiVisualGateTests(unittest.TestCase):
    def test_oracle_and_pr_workflow_are_present_and_use_exact_matrix(self):
        self.assertTrue(ORACLE.is_file(), "the CI visual oracle must be checked in")
        workflow = ROOT / ".github" / "workflows" / "visual-ci.yml"
        self.assertTrue(workflow.is_file(), "the pull-request visual workflow must be checked in")
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("390x844", text)
        self.assertIn("1440x900", text)
        self.assertIn("verificar_ci_visual.py publish", text)

    @unittest.skipUnless(resolve_playwright_module(), "Playwright/Chromium is not installed")
    def test_fixture_with_horizontal_overflow_fails_the_real_browser_oracle(self):
        with tempfile.TemporaryDirectory(prefix="fcmo-ci-visual-overflow-") as tmp:
            root = Path(tmp)
            for locale, route in (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/")):
                page = root / route / "index.html"
                page.parent.mkdir(parents=True, exist_ok=True)
                content = "<h1>Fixture</h1>"
                if locale == "es-419":
                    content += '<div style="width: 500px">overflow regression</div>'
                page.write_text(
                    "<!doctype html><html lang='" + locale + "'><meta charset='utf-8'>"
                    + "<body>" + content + "</body></html>", encoding="utf-8"
                )
            (root / "data").mkdir()
            (root / "data" / "routes.json").write_text(json.dumps([
                {"path": "", "locale": "en"},
                {"path": "es/", "locale": "es-419"},
                {"path": "zh/", "locale": "zh-Hans"},
            ]), encoding="utf-8")
            env = os.environ.copy()
            env["PLAYWRIGHT_MODULE"] = resolve_playwright_module() or ""
            result = subprocess.run(
                [sys.executable, str(ORACLE), str(root)],
                cwd=ROOT, env=env, text=True, capture_output=True, timeout=90,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("horizontal overflow", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
