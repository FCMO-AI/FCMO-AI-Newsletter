from __future__ import annotations

import os
import subprocess
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


if __name__ == "__main__":
    unittest.main()
