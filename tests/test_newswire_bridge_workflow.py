from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ".github" / "workflows" / "newswire-bridge.yml"
REFRESH = ROOT / ".github" / "workflows" / "daily-refresh.yml"
PARTIAL = ROOT / "tools" / "newswire_bridge_partial_locales.py"


class NewswireBridgeWorkflowContractTests(unittest.TestCase):
    """Security/identity contracts for the current freshest-sealed bridge."""

    def text(self) -> str:
        return BRIDGE.read_text(encoding="utf-8")

    def test_bridge_has_only_app_activation_inputs_and_read_only_private_scope(self) -> None:
        text = self.text()
        self.assertIn("FCMO_NEWSWIRE_APP_CLIENT_ID", text)
        self.assertNotIn("FCMO_NEWSWIRE_APP_ID", text)
        self.assertIn("FCMO_NEWSWIRE_APP_PRIVATE_KEY", text)
        self.assertIn("client-id: ${{ vars.FCMO_NEWSWIRE_APP_CLIENT_ID }}", text)
        self.assertIn("repositories: AI-Research-Breakthroughs", text)
        self.assertIn("permission-contents: read", text)
        self.assertNotIn("permission-contents: write", text)
        for forbidden in ("FCMO_NEWSLETTER_" + "PUBLISH_TOKEN", "ANTH" + "ROPIC_API_KEY", "GH_" + "PAT"):
            self.assertNotIn(forbidden, text)

    def test_app_secret_is_only_consumed_by_token_action_on_main(self) -> None:
        text = self.text()
        self.assertIn("if: github.ref == 'refs/heads/main'", text)
        secret_ref = "${{ secrets.FCMO_NEWSWIRE_APP_PRIVATE_KEY }}"
        self.assertEqual(text.count(secret_ref), 1)
        self.assertIn(f"private-key: {secret_ref}", text)
        self.assertNotIn("APP_PRIVATE_KEY:", text)

    def test_private_materialization_avoids_checkout_action_sha_leak(self) -> None:
        text = self.text()
        self.assertNotIn("repository: FCMO-AI/AI-Research-Breakthroughs", text)
        self.assertIn("clone --quiet --depth 1 --single-branch --branch main", text)
        self.assertIn('http.https://github.com/.extraheader=AUTHORIZATION: basic $AUTH', text)
        for marker in ('echo "::add-mask::$AUTH"', 'echo "::add-mask::$READY_SHA"', 'echo "::add-mask::$CURRENT_SHA"'):
            self.assertIn(marker, text)
        self.assertIn("unset AUTH APP_TOKEN READY_SHA CURRENT_SHA SELECTED_SHA", text)

    def test_current_main_is_preferred_only_when_atomic_seal_passes(self) -> None:
        text = self.text()
        self.assertIn('path = Path(os.environ["PRIVATE_DIR_ENV"]) / "state" / "PUBLICATION_READY.json"', text)
        self.assertIn('CURRENT_SHA=$(git -C "$PRIVATE_DIR" rev-parse origin/main)', text)
        self.assertIn('checkout --detach --quiet "$CURRENT_SHA"', text)
        self.assertIn('python tools/publication_seal.py', text)
        self.assertIn('SELECTED_SHA="$CURRENT_SHA"', text)
        self.assertIn('Fresh canonical ARB main passed the complete publication seal.', text)

    def test_failed_current_main_falls_back_to_ancestor_ready_snapshot(self) -> None:
        text = self.text()
        # The bridge unshallows canonical main once; a reachable READY ancestor
        # must already exist locally. Raw-SHA fetches are unnecessary and may be
        # rejected by GitHub even for a valid reachable commit.
        self.assertIn('fetch --quiet --unshallow origin main', text)
        self.assertIn('cat-file -e "$READY_SHA^{commit}"', text)
        self.assertNotIn('fetch --quiet origin "$READY_SHA"', text)
        self.assertIn('merge-base --is-ancestor "$READY_SHA" origin/main', text)
        self.assertIn('checkout --detach --quiet "$READY_SHA"', text)
        self.assertIn('SELECTED_SHA="$READY_SHA"', text)
        # Whichever lane wins, extraction is bound to one exact detached SHA.
        self.assertIn('test "$(git -C "$PRIVATE_DIR" rev-parse HEAD)" = "$SELECTED_SHA"', text)
        self.assertIn('git -C "$PRIVATE_DIR" rev-parse HEAD >"$PRIVATE_SHA"', text)
        self.assertIn('test -z "$(git -C "$PRIVATE_DIR" branch --show-current)"', text)
        self.assertLess(text.index('merge-base --is-ancestor "$READY_SHA" origin/main'), text.index('checkout --detach --quiet "$READY_SHA"'))

    def test_selected_snapshot_is_sealed_again_before_extraction(self) -> None:
        text = self.text()
        # First invocation is a freshness probe on current main; second is the
        # authoritative proof on the immutable SELECTED_SHA. Both must stay.
        self.assertEqual(text.count("python tools/publication_seal.py"), 2)
        second_step = text.index("- name: Prove selected immutable snapshot through ARB's atomic publication seal")
        extraction = text.index("- name: Extract only the already-sanitized release")
        self.assertLess(second_step, extraction)
        segment = text[second_step:extraction]
        self.assertIn('PRIVATE_LOG="$RUNNER_TEMP/fcmo-newswire-private-seal.log"', segment)
        self.assertIn("grep -qx 'SEAL_OK'", segment)
        for retired in (
            "python tools/validate_publication_plane.py", "python tools/build_publication.py --check-determinism",
            "python tools/build_public_release.py", "python tools/build_public_locales.py build",
            "python tools/build_airlock_receipt.py",
        ):
            self.assertNotIn(retired, text)

    def test_private_process_receives_minimal_allowlisted_environment(self) -> None:
        text = self.text()
        self.assertGreaterEqual(text.count("env -i"), 2)
        for allowed in ('"PATH=$PATH"','"HOME=$HOME"','"LANG=C.UTF-8"','"LC_ALL=C.UTF-8"','"ARB_SITE_BASE_PATH=/FCMO-AI-Newsletter"','"ARB_PUBLIC_BASE_URL=https://fcmo-ai.github.io/FCMO-AI-Newsletter"'):
            self.assertIn(allowed, text)
        private = text[text.index("env -i"):text.index("Extract only the already-sanitized release")]
        for forbidden in ("GITHUB_ENV=","GITHUB_OUTPUT=","ACTIONS_RUNTIME_TOKEN=","ACTIONS_ID_TOKEN_REQUEST_TOKEN=","GITHUB_TOKEN="):
            self.assertNotIn(forbidden, private)

    def test_private_execution_logs_are_sanitized_and_destroyed(self) -> None:
        text = self.text()
        self.assertIn("grep -E '^SEAL_FAIL:[A-Z0-9_]+'", text)
        self.assertIn("SEAL_FAIL:UNCLASSIFIED", text)
        self.assertIn('rm -f "$RUNNER_TEMP/fcmo-newswire-private-seal.log"', text)
        self.assertIn('rm -f "$RUNNER_TEMP/fcmo-newswire-current-main-seal.log"', text)

    def test_private_checkout_is_destroyed_before_public_verification(self) -> None:
        text = self.text()
        extract = text.index("- name: Extract only the already-sanitized release")
        verify = text.index("- name: Independently verify the airlocked bytes")
        segment = text[extract:verify]
        self.assertIn('rm -rf "$PRIVATE_DIR"', segment)
        self.assertIn('rm -f "$PRIVATE_SHA"', segment)

    def test_partial_locale_transport_still_proves_strict_privacy_and_symmetric_ids(self) -> None:
        workflow = self.text()
        partial = PARTIAL.read_text(encoding="utf-8")
        self.assertEqual(workflow.count('newswire_bridge_partial_locales.py verify "$RELEASE_DIR"'), 2)
        self.assertIn('newswire_bridge_partial_locales.py stage "$RELEASE_DIR" corpus', workflow)
        # Coverage relaxation is verifier-only and cannot invent/stage prose.
        self.assertIn("strict.verify_release(release, proof)", partial)
        self.assertIn("locale delta contains IDs outside public corpus", partial)
        self.assertIn("native locale delta ID sets differ", partial)
        self.assertIn("shutil.copytree(release, stage, symlinks=False)", partial)
        self.assertNotIn("site/data/i18n", workflow)

    def test_bridge_stages_and_commits_only_corpus(self) -> None:
        text = self.text()
        self.assertIn("git add -A -- corpus", text)
        self.assertIn("git diff --cached --quiet -- ':!corpus'", text)
        self.assertNotRegex(text, re.compile(r"git add (?:-A )?\.(?:\s|$)"))

    def test_bridge_has_hourly_idempotent_recovery_heartbeat(self) -> None:
        text = self.text()
        # Material canonical truth should not wait for a morning-only window.
        # One hourly idempotent heartbeat bounds transport lag while unchanged
        # semantic Airlocks remain no-op.
        self.assertIn("cron: '10 * * * *'", text)
        self.assertEqual(len(re.findall(r"- cron: '[^']+'", text)), 1)
        self.assertIn("unchanged semantic content", text)
        self.assertIn("cancel-in-progress: false", text)

    def test_refresh_is_chained_from_successful_bridge(self) -> None:
        text = REFRESH.read_text(encoding="utf-8")
        self.assertIn("'Pull airlocked newswire with GitHub App'", text)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertNotIn("cron:", text)

    def test_bridge_does_not_need_actions_write_or_api_dispatch(self) -> None:
        text = self.text()
        self.assertNotIn("actions: write", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("daily-refresh.yml/dispatches", text)


if __name__ == "__main__":
    unittest.main()
