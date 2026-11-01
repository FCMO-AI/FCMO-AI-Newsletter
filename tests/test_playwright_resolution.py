from __future__ import annotations

import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from tools.paper import playwright_module


class PlaywrightResolutionTests(unittest.TestCase):
    def test_environment_module_takes_precedence(self):
        with patch.dict(os.environ, {"PLAYWRIGHT_MODULE": "runner-playwright"}):
            with patch.object(playwright_module.subprocess, "run") as run:
                self.assertEqual(playwright_module.resolve_playwright_module(), "runner-playwright")
                run.assert_not_called()

    def test_node_resolves_repository_dependency_when_environment_is_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(playwright_module.shutil, "which", return_value="/usr/bin/node"):
                with patch.object(
                    playwright_module.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, "/repo/node_modules/playwright/index.js", ""),
                ) as run:
                    result = playwright_module.resolve_playwright_module()
        self.assertEqual(result, "/repo/node_modules/playwright/index.js")
        command = run.call_args.args[0]
        self.assertIn("createRequire", command[2])
        self.assertEqual(run.call_args.kwargs["cwd"], playwright_module.ROOT)

    def test_missing_module_has_direct_setup_message(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(playwright_module.shutil, "which", return_value=None):
                self.assertIsNone(playwright_module.resolve_playwright_module())
        self.assertIn("PLAYWRIGHT_MODULE", playwright_module.missing_playwright_message())

    def test_a_missing_browser_skips_locally_but_fails_when_ci_requires_it(self):
        import unittest as _u
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(_u.SkipTest):
                playwright_module.browser_unavailable()
        with patch.dict(os.environ, {"FCMO_REQUIRE_BROWSER": "1"}, clear=True):
            with self.assertRaises(AssertionError) as caught:
                playwright_module.browser_unavailable()
        self.assertIn("FCMO_REQUIRE_BROWSER=1", str(caught.exception))

    def test_browser_tests_in_c6_polish_fail_under_the_requirement_when_playwright_is_absent(self):
        # End to end: run the real test module with no resolvable Playwright and the requirement on -> failures, not skips.
        env = {k: v for k, v in os.environ.items() if k != "PLAYWRIGHT_MODULE"}
        env.update({"FCMO_REQUIRE_BROWSER": "1", "PATH": "/nonexistent"})
        run = subprocess.run([sys.executable, "-m", "unittest", "tests.test_c6_polish.PhoneOpeningFactTests"],
                             cwd=playwright_module.ROOT, env=env, text=True, capture_output=True)
        self.assertNotEqual(run.returncode, 0, run.stderr[-400:])
        self.assertNotIn("skipped", run.stderr)


if __name__ == "__main__":
    unittest.main()
