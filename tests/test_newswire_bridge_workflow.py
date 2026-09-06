from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ".github" / "workflows" / "newswire-bridge.yml"
REFRESH = ROOT / ".github" / "workflows" / "daily-refresh.yml"


# Footnote: this suite is intentionally executable on every publication-boundary
# change so source/ref, secret-scope and private-log regressions cannot reach production.
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
        self.assertNotIn("APP_PRIVATE_KEY:", text)

    def test_private_materialization_avoids_checkout_action_sha_leak(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertNotIn("repository: FCMO-AI/AI-Research-Breakthroughs", text)
        self.assertIn("clone --quiet --depth 1 --single-branch --branch main", text)
        self.assertIn('http.https://github.com/.extraheader=AUTHORIZATION: basic $AUTH', text)
        self.assertIn('echo "::add-mask::$AUTH"', text)
        self.assertIn("unset AUTH APP_TOKEN", text)
        self.assertNotIn("x-access-token:${{", text)

    def test_live_main_is_frozen_to_one_immutable_checkout_before_validation(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        # Footnote: main is permitted as discovery input only because the job captures
        # exactly one HEAD, records its identity privately, and detaches before any
        # validation. Later research commits therefore cannot mutate this transaction.
        self.assertIn("--branch main", text)
        self.assertIn('git -C "$PRIVATE_DIR" rev-parse HEAD >"$PRIVATE_SHA"', text)
        self.assertIn('git -C "$PRIVATE_DIR" checkout --detach --quiet HEAD', text)
        self.assertIn('test -z "$(git -C "$PRIVATE_DIR" branch --show-current)"', text)
        self.assertNotIn("publication-ready", text)

    def test_private_tree_and_source_identity_live_outside_public_workspace(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count('PRIVATE_DIR="$RUNNER_TEMP/fcmo-newswire-private-source"'), 2)
        self.assertGreaterEqual(text.count('PRIVATE_SHA="$RUNNER_TEMP/fcmo-newswire-private-source.sha"'), 2)
        self.assertNotIn("mkdir -p .newswire-private-source", text)
        self.assertNotIn("cd .newswire-private-source", text)
        self.assertIn("git reset --hard origin/main", text)
        self.assertIn("git clean -fdx", text)

    def test_private_process_receives_minimal_allowlisted_environment(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertGreaterEqual(text.count("env -i"), 1)
        for allowed in (
            '"PATH=$PATH"',
            '"HOME=$HOME"',
            '"LANG=C.UTF-8"',
            '"LC_ALL=C.UTF-8"',
            '"ARB_SITE_BASE_PATH=/FCMO-AI-Newsletter"',
            '"ARB_PUBLIC_BASE_URL=https://fcmo-ai.github.io/FCMO-AI-Newsletter"',
        ):
            self.assertIn(allowed, text)
        private_env_block = text[text.index("env -i") : text.index("Extract only the already-sanitized release")]
        for forbidden in (
            "GITHUB_ENV=",
            "GITHUB_OUTPUT=",
            "GITHUB_PATH=",
            "GITHUB_STEP_SUMMARY=",
            "ACTIONS_RUNTIME_TOKEN=",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN=",
            "GITHUB_TOKEN=",
        ):
            self.assertNotIn(forbidden, private_env_block)

    def test_atomic_upstream_seal_is_the_only_private_publication_command(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertEqual(text.count("python tools/publication_seal.py"), 1)
        for retired_direct_call in (
            "python tools/validate_publication_plane.py",
            "python tools/build_publication.py --check-determinism",
            "python tools/build_public_release.py",
            "python tools/build_public_locales.py build",
            "python tools/build_airlock_receipt.py",
        ):
            self.assertNotIn(retired_direct_call, text)

    def test_private_execution_output_exposes_only_safe_reason_codes(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('PRIVATE_LOG="$RUNNER_TEMP/fcmo-newswire-private-seal.log"', text)
        self.assertIn('>"$PRIVATE_LOG" 2>&1', text)
        self.assertIn("grep -E '^SEAL_FAIL:[A-Z0-9_]+'", text)
        self.assertIn("SEAL_FAIL:UNCLASSIFIED", text)
        self.assertIn("grep -qx 'SEAL_OK'", text)
        self.assertGreaterEqual(text.count('rm -f "$PRIVATE_LOG"'), 2)

    def test_private_checkout_is_destroyed_before_public_side_verification(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        extract = text.index("- name: Extract only the already-sanitized release")
        verify = text.index("- name: Independently verify the airlocked bytes")
        segment = text[extract:verify]
        self.assertIn('rm -rf "$PRIVATE_DIR"', segment)
        self.assertIn('rm -f "$PRIVATE_SHA"', segment)

    def test_residual_private_state_is_always_destroyed(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        cleanup = text.index("- name: Destroy any residual private bridge state")
        self.assertIn("if: always()", text[cleanup:])
        tail = text[cleanup:]
        for marker in (
            'rm -rf "$RUNNER_TEMP/fcmo-newswire-private-source"',
            'rm -f "$RUNNER_TEMP/fcmo-newswire-private-source.sha"',
            'rm -f "$RUNNER_TEMP/fcmo-newswire-private-seal.log"',
            'rm -rf "$RUNNER_TEMP/fcmo-newswire-airlocked-release"',
        ):
            self.assertIn(marker, tail)

    def test_bridge_stages_and_commits_only_corpus(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("git add -A -- corpus", text)
        self.assertIn("git diff --cached --quiet -- ':!corpus'", text)
        self.assertNotRegex(text, re.compile(r"git add (?:-A )?\.(?:\s|$)"))

    def test_bridge_has_redundant_staggered_daily_attempts(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        for cron in ("10 13", "37 13", "11 14", "47 14"):
            self.assertIn(f"cron: '{cron} * * *'", text)
        self.assertIn("07:10", text)
        self.assertIn("07:37", text)
        self.assertIn("08:11", text)
        self.assertIn("08:47", text)

    def test_refresh_is_chained_from_successful_bridge(self) -> None:
        text = REFRESH.read_text(encoding="utf-8")
        self.assertIn("'Pull airlocked newswire with GitHub App'", text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertNotIn("cron:", text)

    def test_bridge_does_not_need_actions_write_or_api_dispatch(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertNotIn("actions: write", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("daily-refresh.yml/dispatches", text)


if __name__ == "__main__":
    unittest.main()
