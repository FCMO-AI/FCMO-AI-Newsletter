from __future__ import annotations

import re
import unittest
from pathlib import Path

try:  # PyYAML is optional: CI's setup-python has no third-party packages.
    import yaml
except ImportError:  # pragma: no cover - depends on the runner
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / ".github" / "workflows" / "newswire-bridge.yml"
REFRESH = ROOT / ".github" / "workflows" / "daily-refresh.yml"
HEALTH = ROOT / ".github" / "workflows" / "newsroom-health.yml"
PAGES = ROOT / ".github" / "workflows" / "pages.yml"
WORKFLOWS = ROOT / ".github" / "workflows"
PARTIAL = ROOT / "tools" / "newswire_bridge_partial_locales.py"
WIRE = ROOT / "tools" / "wire_status.py"


def load_workflow(case: unittest.TestCase, path: Path) -> dict:
    if yaml is None:
        case.skipTest("PyYAML is not installed")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


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
        # Neither private identities nor authentication headers are sent even to
        # workflow commands. Whole-step suppression protects git errors too.
        self.assertNotIn("::add-mask::", text)
        self.assertIn("exec 3>&1 >/dev/null 2>&1", text)
        self.assertIn("unset AUTH APP_TOKEN READY_SHA CURRENT_SHA SELECTED_SHA", text)

    def test_current_main_is_preferred_only_when_seal_and_integrity_ratchet_pass(self) -> None:
        text = self.text()
        self.assertIn('path = Path(os.environ["PRIVATE_DIR_ENV"]) / "state" / "PUBLICATION_READY.json"', text)
        self.assertIn('CURRENT_SHA=$(git -C "$PRIVATE_DIR" rev-parse origin/main)', text)
        self.assertIn('checkout --detach --quiet "$CURRENT_SHA"', text)
        self.assertIn('python tools/publication_seal.py', text)
        self.assertIn('python tools/validate_integrity_ratchet.py --json', text)
        self.assertIn('SELECTED_SHA="$CURRENT_SHA"', text)
        self.assertIn(
            'Fresh canonical ARB main passed the publication seal and no-new-debt ratchet.',
            text,
        )
        self.assertNotRegex(text, r"SAFE_REASON=\$\(")

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

    def test_private_snapshot_sha_uses_one_handoff_path_everywhere(self) -> None:
        text = self.text()
        self.assertNotIn("fcmo-newswire-private.sha", text)
        self.assertIn("fcmo-newswire-private-source.sha", text)
        self.assertIn("selected private snapshot receipt is missing", text)
        self.assertIn("selected private snapshot SHA is empty", text)

    def test_integrity_probe_targets_current_main_and_restores_selected_snapshot(self) -> None:
        text = self.text()
        step = text.index("- name: Measure current canonical ARB integrity on the working GitHub runner")
        seal = text.index("- name: Prove selected immutable snapshot through ARB's atomic publication seal")
        segment = text[step:seal]
        self.assertIn('PRIVATE_SHA="$RUNNER_TEMP/fcmo-newswire-private-source.sha"', segment)
        self.assertIn('test -s "$PRIVATE_SHA"', segment)
        self.assertIn('read -r SELECTED_SHA < "$PRIVATE_SHA"', segment)
        self.assertIn('test -n "$SELECTED_SHA"', segment)
        self.assertIn('CURRENT_SHA="$(git -C "$PRIVATE_DIR" rev-parse origin/main)"', segment)
        self.assertIn('git checkout --detach --quiet "$CURRENT_SHA"', segment)
        self.assertIn('git checkout --detach --quiet "$SELECTED_SHA"', segment)
        self.assertIn('test "$(git rev-parse HEAD)" = "$SELECTED_SHA"', segment)
        self.assertIn("python tools/validate_integrity_ratchet.py --json", segment)
        self.assertIn("python tools/arb.py orient --json", segment)

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
        self.assertNotRegex(text, r"SAFE_REASON=\$\(")
        self.assertNotIn("grep -E '^SEAL_FAIL:", text)
        self.assertIn("exec 3>&1 >/dev/null 2>&1", text)
        self.assertIn('rm -f "$RUNNER_TEMP/fcmo-newswire-private-seal.log"', text)
        self.assertIn('rm -f "$RUNNER_TEMP/fcmo-newswire-current-main-seal.log"', text)

    def test_private_checkout_is_destroyed_before_public_verification(self) -> None:
        text = self.text()
        extract = text.index("- name: Extract only the already-sanitized release")
        verify = text.index("- name: Independently verify the airlocked bytes")
        segment = text[extract:verify]
        self.assertIn('rm -rf "$RUNNER_TEMP/fcmo-newswire-private-source"', segment)
        self.assertIn('test ! -e "$PRIVATE_DIR"', segment)
        self.assertIn('rm -f "$PRIVATE_SHA"', segment)

    def test_partial_locale_transport_still_proves_strict_privacy_and_symmetric_ids(self) -> None:
        workflow = self.text()
        partial = PARTIAL.read_text(encoding="utf-8")
        self.assertEqual(workflow.count('newswire_bridge_partial_locales.py verify "$RELEASE_DIR"'), 2)
        # Staging goes through wire_status.py stage, which keeps the newsroom-owned
        # files and delegates the swap to the strict partial-locale stager.
        self.assertIn("python tools/wire_status.py stage", workflow)
        self.assertIn('--release "$RELEASE_DIR"', workflow)
        wire = WIRE.read_text(encoding="utf-8")
        self.assertIn('"newswire_bridge_partial_locales.py"), "stage"', wire)
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

    def test_bridge_retries_verified_corpus_transaction_across_public_main_races(self) -> None:
        text = self.text()
        step = text.index("- name: Record the wire status and commit on top of the newest public main")
        cleanup = text.index("- name: Destroy any residual private bridge state")
        segment = text[step:cleanup]
        self.assertIn('cp -a corpus "$INCOMING"', segment)
        self.assertIn("for attempt in 1 2 3 4 5", segment)
        self.assertIn("git fetch --quiet origin main", segment)
        self.assertIn("git reset --hard origin/main", segment)
        self.assertIn('cp -a "$INCOMING" corpus', segment)
        # The sealed bytes are reverified without the newsroom-owned files.
        self.assertIn("python tools/wire_status.py sealed-view --corpus corpus", segment)
        self.assertIn('newswire_bridge_partial_locales.py verify "$RUNNER_TEMP/fcmo-newswire-sealed-view"', segment)
        self.assertIn("git add -A -- corpus", segment)
        self.assertIn("if git push origin HEAD:main; then", segment)
        self.assertIn("retrying from newest main", segment)
        self.assertIn("did not converge after 5 optimistic retries", segment)
        self.assertNotIn("--force", segment)

    def test_bridge_has_hourly_idempotent_recovery_heartbeat(self) -> None:
        text = self.text()
        # Material canonical truth should not wait for a morning-only window.
        # One hourly idempotent heartbeat bounds transport lag while unchanged
        # semantic Airlocks remain no-op.
        self.assertIn("cron: '10 * * * *'", text)
        self.assertEqual(len(re.findall(r"- cron: '[^']+'", text)), 1)
        self.assertIn("unchanged semantic content", text)
        self.assertIn("group: fcmo-newswire-bridge-v2", text)
        self.assertIn("cancel-in-progress: true", text)

    def test_refresh_is_chained_from_every_bridge_run(self) -> None:
        text = REFRESH.read_text(encoding="utf-8")
        self.assertIn("'Pull airlocked newswire with GitHub App'", text)
        # A failing bridge must reach readers as a delayed edition, so the refresh
        # runs on every bridge conclusion; the preflight decides what to do.
        self.assertNotIn("github.event.workflow_run.conclusion == 'success'", text)
        self.assertIn("types: [completed]", text)
        self.assertNotIn("cron:", text)
        self.assertIn("- '!corpus/wire-status.json'", text)

    def test_bridge_does_not_need_actions_write_or_api_dispatch(self) -> None:
        text = self.text()
        self.assertNotIn("actions: write", text)
        self.assertNotIn("gh api", text)
        self.assertNotIn("daily-refresh.yml/dispatches", text)

    # --- wire liveness, drills and log hygiene (WP-A1) ---------------------------------
    def test_bridge_offers_the_two_safety_drills_on_manual_runs_only(self) -> None:
        doc = load_workflow(self, BRIDGE)
        dispatch = doc[True]["workflow_dispatch"]
        self.assertEqual(dispatch["inputs"]["drill"]["options"], ["", "force_checkpoint", "regressing_snapshot"])
        self.assertEqual(doc["env"]["FCMO_DRILL"], "${{ github.event_name == 'workflow_dispatch' && inputs.drill || '' }}")
        text = self.text()
        self.assertIn("if test \"$FCMO_DRILL\" = 'force_checkpoint'; then", text)
        self.assertIn("DRILL_FORCE_CHECKPOINT", text)
        self.assertIn('--drill "$FCMO_DRILL"', text)

    def test_every_run_records_wire_status_even_after_a_failure(self) -> None:
        steps = load_workflow(self, BRIDGE)["jobs"]["bridge"]["steps"]
        by_name = {step.get("name"): step for step in steps}
        record = by_name["Record the wire status and commit on top of the newest public main"]
        self.assertEqual(record["if"], "${{ !cancelled() }}")
        run = record["run"]
        self.assertIn("python tools/wire_status.py write", run)
        self.assertIn("--transport \"$TRANSPORT\"", run)
        self.assertIn("cp \"$CODES/wire-status.json\" corpus/wire-status.json", run)
        for code in ("APP_NOT_CONFIGURED", "TOKEN_MINT_FAILED", "STAGE_FAILED"):
            self.assertIn(code, run)
        self.assertIn("git commit -q -m 'corpus: record newswire wire status'", run)
        self.assertIn('if test "$TRANSPORT" != OK; then', run)
        ids = {step.get("id") for step in steps}
        for step_id in ("config", "app-token", "select", "probe", "seal", "extract", "verify", "rebase", "guard", "stage"):
            self.assertIn(step_id, ids)
        guard = by_name["Guard the verified candidate against the published corpus"]["run"]
        self.assertIn("python tools/wire_status.py guard", guard)
        self.assertEqual(by_name["Atomically replace only corpus/"]["if"], "steps.guard.outputs.stage == 'true'")

    def test_probe_diagnostics_never_reach_the_public_log(self) -> None:
        text = self.text()
        self.assertIsNone(re.search(r"ARB_TOOL_OUTPUT|tee|>> *\$GITHUB_STEP_SUMMARY", text))
        self.assertNotIn("::group::", text)
        probe = text[text.index("- name: Measure current canonical ARB integrity"):text.index("- name: Prove selected immutable snapshot")]
        self.assertIn('bash -o pipefail -c "$cmd" 3>&- </dev/null >"$PROBE_LOG" 2>&1', probe)
        self.assertIn('rm -f "$RUNNER_TEMP/fcmo-newswire-probe.log"', probe)
        for code in ("INTEGRITY_RATCHET", "TEST_SUITE", "OPERATIONAL_PROBES", "NATIVE_EDITION_COVERAGE"):
            self.assertIn(f"{code}|python ", probe)
        self.assertIn("python tools/check_native_edition_coverage.py --recent-days 7", probe)
        self.assertIn('echo "::warning::ARB current-main probe failed: $code"', probe)

    def test_retired_workflows_are_gone(self) -> None:
        self.assertIn("exec 3>&1 >/dev/null 2>&1", (WORKFLOWS / "translation-source-health.yml").read_text())
        self.assertFalse((WORKFLOWS / "backfill-arb-native-locales-once.yml").exists())

    def test_owned_workflows_use_current_action_majors(self) -> None:
        for path in (BRIDGE, REFRESH, HEALTH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("actions/setup-python@v5", text, path.name)
            self.assertNotIn("actions/upload-artifact@v4", text, path.name)
            self.assertNotIn("actions/checkout@v4", text, path.name)

    def test_refresh_reads_wire_status_and_has_a_status_only_path(self) -> None:
        doc = load_workflow(self, REFRESH)
        steps = doc["jobs"]["refresh"]["steps"]
        preflight = next(step for step in steps if step.get("id") == "preflight")
        self.assertIn("python tools/newsroom_receipt.py preflight", preflight["run"])
        self.assertIn('if test "$rc" -gt 1; then exit "$rc"; fi', preflight["run"])
        conditions = {step.get("name"): step.get("if") for step in steps}
        self.assertEqual(conditions["Regenerate the canonical public source from the corpus"], "steps.preflight.outputs.path == 'rebuild'")
        self.assertEqual(conditions["Record only the edition state (no material change)"], "steps.preflight.outputs.path == 'status'")
        text = REFRESH.read_text(encoding="utf-8")
        self.assertNotIn("steps.airlock.outputs", text)
        self.assertIn("finalize --wire-status corpus/wire-status.json", text)
        self.assertIn("':!corpus/wire-status.json'", text)
        preview = doc["jobs"]["preview"]
        self.assertEqual(preview["permissions"], {"contents": "read"})
        self.assertIn("drill_now_offset_h", doc[True]["workflow_dispatch"]["inputs"])
        preview_run = "\n".join(step.get("run", "") for step in preview["steps"])
        self.assertNotIn("git push", preview_run)
        self.assertIn("python -m tools.paper.build", preview_run)
        self.assertIn('--status "$STATUS"', preview_run)

    def test_health_splits_serving_from_freshness_and_publishes_health_state(self) -> None:
        doc = load_workflow(self, HEALTH)
        jobs = doc["jobs"]
        self.assertEqual(set(jobs), {"serving-health", "publication-freshness", "editorial-freshness", "translation-health", "health-state"})
        serving = "\n".join(step.get("run", "") for step in jobs["serving-health"]["steps"])
        self.assertIn("verify_live_newsroom.py --serving-only", serving)
        self.assertNotIn("--require-airlock", HEALTH.read_text(encoding="utf-8"))
        freshness = "\n".join(step.get("run", "") for step in jobs["publication-freshness"]["steps"])
        self.assertIn("python tools/wire_status.py classify --wire-status corpus/wire-status.json", freshness)
        editorial = "\n".join(step.get("run", "") for step in jobs["editorial-freshness"]["steps"])
        self.assertIn("editorial_freshness.py check", editorial)
        state = jobs["health-state"]
        self.assertIn("always()", state["if"])
        self.assertEqual(set(state["needs"]), {"serving-health", "publication-freshness", "editorial-freshness", "translation-health"})
        upload = next(step for step in state["steps"] if str(step.get("uses", "")).startswith("actions/upload-artifact@"))
        self.assertEqual(upload["uses"], "actions/upload-artifact@v6")
        self.assertEqual(upload["with"]["name"], "health-state")
        self.assertEqual(upload["with"]["path"], "health/health-state.json")

    def test_story_layer_flows_through_paper_gates_browser_and_deploy(self) -> None:
        refresh = REFRESH.read_text(encoding="utf-8")
        pages = PAGES.read_text(encoding="utf-8")
        pipeline = refresh + "\n" + pages
        positions = [
            pipeline.index("python -m tools.story_layer build"),
            pipeline.index("python tools/paper/build.py"),
            pipeline.index("python tools/gates/run_all.py publish"),
            pipeline.index("python tests/oraculos/verificar_paper.py publish"),
            pipeline.index("uses: actions/deploy-pages@v4"),
        ]
        self.assertEqual(positions, sorted(positions))
        for retired in (
            "python tools/build_final_release.py",
            "python tools/build_ready_receipt.py",
            "python tools/verify_release.py",
        ):
            self.assertNotIn(retired, refresh)
        self.assertIn("git add -A -- release-src release-overlay site READY_TO_PUBLISH.md", refresh)
        self.assertNotIn("python tools/build_final_release.py", refresh)


if __name__ == "__main__":
    unittest.main()
