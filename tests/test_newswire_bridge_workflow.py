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
        self.assertIn("FCMO_NEWSWIRE_APP_CLIENT_ID", text)
        self.assertNotIn("FCMO_NEWSWIRE_APP_ID", text)
        self.assertIn("FCMO_NEWSWIRE_APP_PRIVATE_KEY", text)
        self.assertIn("client-id: ${{ vars.FCMO_NEWSWIRE_APP_CLIENT_ID }}", text)
        self.assertNotIn("app-id:", text)
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

    def test_app_secret_is_only_consumed_by_token_action_on_main(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        secret_ref = "${{ secrets.FCMO_NEWSWIRE_APP_PRIVATE_KEY }}"
        self.assertEqual(text.count(secret_ref), 1)
        self.assertIn(f"private-key: {secret_ref}", text)
        # Footnote: never route the PEM through a shell env merely to test whether
        # it exists. The token action is a smaller secret-consumption surface.
        self.assertNotIn("APP_PRIVATE_KEY:", text)

    def test_private_materialization_avoids_checkout_action_sha_leak(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        # Footnote: actions/checkout is fine for this public repository, but using
        # it with repository: private-ARB would print the resolved private SHA into
        # the public workflow log. The private source must use quiet Git transport.
        self.assertNotIn("repository: FCMO-AI/AI-Research-Breakthroughs", text)
        self.assertIn("clone --quiet --depth 1 --branch main", text)
        self.assertIn('http.https://github.com/.extraheader=AUTHORIZATION: basic $AUTH', text)
        self.assertIn('echo "::add-mask::$AUTH"', text)
        self.assertIn("unset AUTH APP_TOKEN", text)
        self.assertNotIn("x-access-token:${{", text)

    def test_private_execution_output_never_reaches_public_log(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('PRIVATE_LOG="$RUNNER_TEMP/fcmo-newswire-private-tests.log"', text)
        self.assertIn('PRIVATE_LOG="$RUNNER_TEMP/fcmo-newswire-private-build.log"', text)
        self.assertGreaterEqual(text.count('>"$PRIVATE_LOG" 2>&1'), 2)
        self.assertGreaterEqual(text.count('rm -f "$PRIVATE_LOG"'), 6)
        self.assertNotIn("unittest discover -s tests -v", text)

    def test_private_checkout_is_destroyed_before_public_side_verification(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        destroy = text.index("rm -rf .newswire-private-source")
        verify = text.index("python tools/newswire_bridge.py verify")
        stage = text.index("python tools/newswire_bridge.py stage")
        self.assertLess(destroy, verify)
        self.assertLess(verify, stage)

    def test_residual_private_state_is_always_destroyed(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        cleanup = text.index("- name: Destroy any residual private bridge state")
        self.assertIn("if: always()", text[cleanup:])
        tail = text[cleanup:]
        for marker in (
            "rm -rf .newswire-private-source",
            'rm -f "$RUNNER_TEMP/fcmo-newswire-private-tests.log"',
            'rm -f "$RUNNER_TEMP/fcmo-newswire-private-build.log"',
            'rm -rf "$RUNNER_TEMP/fcmo-newswire-airlocked-release"',
        ):
            self.assertIn(marker, tail)

    def test_bridge_stages_and_commits_only_corpus(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("git add -A -- corpus", text)
        self.assertIn("git diff --cached --quiet -- ':!corpus'", text)
        self.assertNotRegex(text, re.compile(r"git add (?:-A )?\.(?:\s|$)"))

    def test_bridge_cadence_waits_for_settled_six_am_research(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("07:10 America/Mexico_City", text)
        self.assertIn("cron: '10 13 * * *'", text)

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
