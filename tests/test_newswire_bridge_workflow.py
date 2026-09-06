from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ".github" / "workflows" / "newswire-bridge.yml"
REFRESH = ROOT / ".github" / "workflows" / "daily-refresh.yml"


class NewswireBridgeWorkflowContractTests(unittest.TestCase):
    def test_bridge_has_only_app_activation_inputs_and_read_only_private_scope(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("FCMO_NEWSWIRE_APP_ID", text)
        self.assertIn("FCMO_NEWSWIRE_APP_PRIVATE_KEY", text)
        self.assertIn("repositories: AI-Research-Breakthroughs", text)
        self.assertIn("permission-contents: read", text)
        self.assertNotIn("permission-contents: write", text)
        # Footnote: construct retired credential names from fragments so the test
        # protects against regressions without becoming a false positive itself.
        for forbidden in (
            "FCMO_NEWSLETTER_" + "PUBLISH_TOKEN",
            "ANTH" + "ROPIC_API_KEY",
            "GH_" + "PAT",
        ):
            self.assertNotIn(forbidden, text)

    def test_private_checkout_is_destroyed_before_public_side_verification(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        destroy = text.index("rm -rf .newswire-private-source")
        verify = text.index("python tools/newswire_bridge.py verify")
        stage = text.index("python tools/newswire_bridge.py stage")
        self.assertLess(destroy, verify)
        self.assertLess(verify, stage)

    def test_bridge_stages_and_commits_only_corpus(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("git add -A -- corpus", text)
        self.assertIn("git diff --cached --quiet -- ':!corpus'", text)
        self.assertNotRegex(text, re.compile(r"git add (?:-A )?\.(?:\s|$)"))

    def test_refresh_is_chained_from_successful_bridge(self) -> None:
        text = REFRESH.read_text(encoding="utf-8")
        self.assertIn("'Pull airlocked newswire with GitHub App'", text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        # Footnote: the bridge owns the daily cadence. A second scheduled refresh
        # would create duplicate races and confusing stale-heartbeat reds.
        self.assertNotIn("cron:", text)

    def test_bridge_does_not_need_actions_write_or_api_dispatch(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertNotIn("actions: write", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("daily-refresh.yml/dispatches", text)


if __name__ == "__main__":
    unittest.main()
