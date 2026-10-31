"""Regression tests for the repository-wide browser availability policy."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrowserRequirementTests(unittest.TestCase):
    def run_probe(self, *, required: bool = False, ci: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PLAYWRIGHT_MODULE"] = "/nonexistent/playwright"
        env.pop("FCMO_REQUIRE_BROWSER", None)
        env.pop("CI", None)
        if required:
            env["FCMO_REQUIRE_BROWSER"] = "1"
        if ci:
            env["CI"] = "true"
        probe = textwrap.dedent(
            """
            import unittest
            from tools.paper.playwright_module import resolve_playwright_module
            from tests._browser import skip_unless_browser

            class BrowserCase(unittest.TestCase):
                @skip_unless_browser(resolve_playwright_module, "Playwright/Chromium is not installed")
                def test_browser_path(self):
                    pass

            unittest.main(verbosity=2)
            """
        )
        return subprocess.run(
            [sys.executable, "-c", probe],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_browser_skips_locally_but_fails_when_required(self):
        local = self.run_probe()
        self.assertEqual(local.returncode, 0, local.stdout + local.stderr)
        self.assertIn("skipped", local.stderr)

        required = self.run_probe(required=True)
        self.assertNotEqual(required.returncode, 0, required.stdout + required.stderr)
        self.assertIn("BROWSER_UNAVAILABLE (FCMO_REQUIRE_BROWSER)", required.stdout + required.stderr)

    def test_ci_also_requires_a_browser(self):
        result = self.run_probe(ci=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("BROWSER_UNAVAILABLE (FCMO_REQUIRE_BROWSER)", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
