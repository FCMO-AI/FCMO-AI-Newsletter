#!/usr/bin/env python3
"""Adversarial regressions for calibration v6 source-enumerated coverage."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "calibration_v6", HERE / "proof_spine_calibration_ledger_v6.py"
)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
assert SPEC.loader is not None
SPEC.loader.exec_module(m)

FED_SPEC = importlib.util.spec_from_file_location(
    "proof_spine_federation_v6_integration", HERE / "proof_spine_federation.py"
)
federation = importlib.util.module_from_spec(FED_SPEC)
sys.modules[FED_SPEC.name] = federation
assert FED_SPEC.loader is not None
FED_SPEC.loader.exec_module(federation)

WITNESS_SPEC = importlib.util.spec_from_file_location(
    "proof_spine_action_witness_v6_integration", HERE / "proof_spine_action_witness.py"
)
action_witness = importlib.util.module_from_spec(WITNESS_SPEC)
sys.modules[WITNESS_SPEC.name] = action_witness
assert WITNESS_SPEC.loader is not None
WITNESS_SPEC.loader.exec_module(action_witness)

PLAN_PATH = "commons/experiments/FCMO_PROOF_SPINE_CALIBRATION_PLAN_V6_TEST.json"
PLAN_ID = "fcmo-proof-spine-v6-test"
PLAN_TIME = "2026-09-18T05:50:00+00:00"
GATE_TIME = "2026-09-18T06:00:00Z"
D2 = "sha256:" + "2" * 64


def plan() -> dict:
    return {
        "schema_version": 1,
        "kind": m.v5.PLAN_KIND,
        "authority": m.v5.PLAN_AUTHORITY,
        "plan_id": PLAN_ID,
        "authored_at": "2026-09-18T05:45:00Z",
        "sampling_mode": m.v5.SAMPLING_MODE,
        "outcome_blind": True,
        "registered_gates": [
            {
                "project_id": "newsletter",
                "repository": "FCMO-AI/FCMO-AI-Newsletter",
                "gate_id": "candidate_may_enter_deploy",
            }
        ],
        "notes": ["Enroll every qualifying future gate execution."],
    }


def git_repo_with_plan(p: dict) -> tuple[tempfile.TemporaryDirectory, Path, str, str]:
    temp = tempfile.TemporaryDirectory(prefix="proof-spine-v6-git-")
    root = Path(temp.name)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "FCMO Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    target = root / PLAN_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps([p], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", PLAN_PATH], check=True)
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = PLAN_TIME
    env["GIT_COMMITTER_DATE"] = PLAN_TIME
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "Register v6 plan"], check=True, env=env)
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    committed_at = subprocess.check_output(
        ["git", "-C", str(root), "show", "-s", "--format=%cI", sha], text=True
    ).strip()
    return temp, root, sha, committed_at


def registration(p: dict, sha: str, committed_at: str) -> dict:
    return {
        "schema_version": 1,
        "kind": m.v5.REGISTRATION_KIND,
        "authority": m.v5.PLAN_AUTHORITY,
        "plan_id": PLAN_ID,
        "plan_digest": m.v5.canonical_digest(p),
        "repository": "FCMO-AI/FCMO-Agent-Hub",
        "path": PLAN_PATH,
        "commit_sha": sha,
        "committed_at": committed_at,
        "evidence_refs": [f"git-commit:{sha}", f"git-path:{PLAN_PATH}"],
    }


def decision_receipt(*, decision: str = "OPEN") -> dict:
    return {
        "schema_version": 1,
        "kind": m.DECISION_RECEIPT_KIND,
        "authority": "EVIDENCE_ONLY",
        "mode": "FCMO_PROOF_SPINE_PROJECT",
        "evaluated_at": GATE_TIME,
        "context": {
            "project_id": "newsletter",
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "source_sha": "abc123",
            "gate_scope": "candidate_native_editions",
        },
        "proofspec_digest": "sha256:" + "a" * 64,
        "source_evidence_digest": "sha256:" + "d" * 64,
        "effective_evidence_digest": "sha256:" + "b" * 64,
        "proof_report_digest": "sha256:" + "e" * 64,
        "gate_decisions": {
            "candidate_may_enter_deploy": {
                "state": decision,
                "proof_state": "VALID" if decision == "OPEN" else "INVALID",
                "reason": "VALID" if decision == "OPEN" else "INVALID",
            }
        },
    }


D1 = m.v5.canonical_digest(decision_receipt())


def case(
    *,
    digest: str = D1,
    case_id: str = "case-1",
    episode_id: str = "episode-1",
    decision: str = "OPEN",
    actual: str = "SHOULD_ALLOW",
) -> dict:
    subject = {"source_sha": "abc123", "gate_scope": "candidate_native_editions"}
    return {
        "schema_version": 4,
        "kind": "FCMO_PROOF_SPINE_CALIBRATION_CASE",
        "authority": "EVIDENCE_ONLY",
        "case_id": case_id,
        "episode_id": episode_id,
        "subject": subject,
        "project": {"id": "newsletter", "repository": "FCMO-AI/FCMO-AI-Newsletter"},
        "gate": {
            "id": "candidate_may_enter_deploy",
            "decision": decision,
            "reason": "VALID" if decision == "OPEN" else "INVALID",
            "observed_at": GATE_TIME,
            "provenance": {
                "state": "EXECUTED",
                "mechanism_id": "proof-spine-v6-test-gate",
                "evaluated_at": GATE_TIME,
                "evidence_refs": ["receipt:test"],
                "measurement_roots": ["spine:gate-measurement"],
                "proofspec_digest": "sha256:" + "a" * 64,
                "effective_evidence_digest": "sha256:" + "b" * 64,
                "decision_receipt_digest": digest,
                "decision_receipt_kind": "FCMO_PROOF_SPINE_DECISION_RECEIPT",
            },
        },
        "action": {"occurred": False},
        "adjudication": {
            "source_authority": "PROJECT_LOCAL",
            "state": actual,
            "relation_to_spine": "INDEPENDENT_OF_SPINE",
            "observed_at": "2026-09-18T06:05:00Z",
            "subject": subject,
            "basis": "Independent project-local postcondition",
            "mechanism": {
                "id": "project-local-oracle",
                "origin": "PREEXISTING_PROJECT_LOCAL",
                "established_at": "2026-09-18T05:00:00Z",
                "evidence_refs": ["workflow:project-local-oracle"],
                "measurement_roots": ["project:independent-postcondition"],
            },
        },
        "evidence_refs": ["run:test"],
        "enrollment": {
            "mode": "PROSPECTIVE",
            "plan_id": PLAN_ID,
            "plan_digest": m.v5.canonical_digest(plan()),
        },
    }


def coverage(
    digests: list[str] | None = None,
    *,
    gate_id: str = "candidate_may_enter_deploy",
    coverage_id: str = "newsletter-predeploy-window-001",
    observed_through: str = "2026-09-18T06:10:00Z",
) -> dict:
    selected = [D1] if digests is None else digests
    gate = {
        "project_id": "newsletter",
        "repository": "FCMO-AI/FCMO-AI-Newsletter",
        "gate_id": gate_id,
    }
    source_snapshot = {
        "schema_version": 1,
        "kind": m.COVERAGE_SNAPSHOT_KIND,
        "authority": m.COVERAGE_SNAPSHOT_AUTHORITY,
        "gate": copy.deepcopy(gate),
        "window": {
            "observed_from": PLAN_TIME,
            "observed_through": observed_through,
        },
        "relation_to_spine": m.COVERAGE_RELATION,
        "origin": "SOURCE_NATIVE_PLATFORM",
        "mechanism_id": "source-native-workflow-run-enumerator",
        "observed_at": "2026-09-18T06:11:00Z",
        "evidence_refs": ["source-run-index:snapshot-001"],
        "measurement_roots": ["platform:workflow-run-index"],
        "decision_receipt_digests": list(selected),
        "source_event_count": len(selected),
    }
    return {
        "schema_version": 1,
        "kind": m.COVERAGE_KIND,
        "authority": m.COVERAGE_AUTHORITY,
        "coverage_id": coverage_id,
        "plan_id": PLAN_ID,
        "gate": gate,
        "observed_from": PLAN_TIME,
        "observed_through": observed_through,
        "decision_receipt_digests": list(selected),
        "enumeration": {
            "state": m.COVERAGE_STATE,
            "relation_to_spine": m.COVERAGE_RELATION,
            "origin": "SOURCE_NATIVE_PLATFORM",
            "mechanism_id": "source-native-workflow-run-enumerator",
            "observed_at": "2026-09-18T06:11:00Z",
            "evidence_refs": ["source-run-index:snapshot-001"],
            "measurement_roots": ["platform:workflow-run-index"],
            "source_snapshot": source_snapshot,
            "source_snapshot_digest": m.v5.canonical_digest(source_snapshot),
            "source_event_count": len(selected),
        },
    }


class CalibrationV6Tests(unittest.TestCase):
    def _occurred_case(self) -> dict:
        c = case()
        c["action"] = {
            "occurred": True,
            "kind": "deployment",
            "observed_at": "2026-09-18T06:02:00Z",
            "subject": copy.deepcopy(c["subject"]),
        }
        return c

    def _exact_action_witness(self) -> dict:
        contract = {
            "schema_version": 1,
            "kind": action_witness.CONTRACT_KIND,
            "gate_id": "candidate_may_enter_deploy",
            "action_kind": "deployment",
            "direct_subject_keys": ["source_sha", "gate_scope"],
            "continuity_subject_keys": [],
            "time_boundary_preference": ["created_at"],
            "require_exact_decision_receipt": True,
        }
        action = {
            "schema_version": 1,
            "kind": action_witness.ACTION_KIND,
            "action_kind": "deployment",
            "action_id": "fixture:deploy-001",
            "outcome": "success",
            "time_boundaries": {"created_at": "2026-09-18T06:02:00Z"},
            "subject": {
                "source_sha": "abc123",
                "gate_scope": "candidate_native_editions",
            },
        }
        return action_witness.evaluate_action_witness(
            contract,
            decision_receipt(),
            action,
        )

    def test_reported_action_does_not_manufacture_verified_lead_time(self):
        p, root, reg = self.setup_bundle()
        c = self._occurred_case()
        report = m.calibrate(
            [p],
            [reg],
            [coverage()],
            [decision_receipt()],
            [c],
            git_root=root,
        )
        event = report["events"][0]
        self.assertEqual(event["classification"], "TRUE_ALLOW")
        self.assertEqual(event["reported_lead_time_seconds"], 120.0)
        self.assertIsNone(event["lead_time_seconds"])
        self.assertEqual(
            event["consequence_evidence"]["state"],
            "ACTION_OBSERVED_WITHOUT_EXACT_WITNESS",
        )
        self.assertFalse(event["consequence_evidence"]["prevention_evidence"])

    def test_exact_action_witness_upgrades_consequence_evidence_only(self):
        p, root, reg = self.setup_bundle()
        c = self._occurred_case()
        witness = self._exact_action_witness()
        report = m.calibrate(
            [p],
            [reg],
            [coverage()],
            [decision_receipt()],
            [c],
            action_witnesses=[witness],
            git_root=root,
        )
        event = report["events"][0]
        self.assertEqual(event["classification"], "TRUE_ALLOW")
        self.assertEqual(
            event["consequence_evidence"]["state"],
            "ACTION_OBSERVED_EXACT_WITNESS",
        )
        self.assertEqual(event["lead_time_seconds"], 120.0)
        self.assertEqual(
            event["consequence_evidence"]["witness_digest"],
            witness["witness_digest"],
        )
        self.assertFalse(event["consequence_evidence"]["prevention_evidence"])

    def test_equivalent_timestamp_spellings_preserve_exact_consequence_binding(self):
        p, root, reg = self.setup_bundle()
        c = self._occurred_case()
        # Footnote: the witness carries the fixture's Z spelling while this case uses
        # the semantically identical +00:00 form. Exactness applies to the decision
        # receipt bytes and action identity, not to redundant UTC typography.
        c["action"]["observed_at"] = "2026-09-18T06:02:00+00:00"
        witness = self._exact_action_witness()
        report = m.calibrate(
            [p],
            [reg],
            [coverage()],
            [decision_receipt()],
            [c],
            action_witnesses=[witness],
            git_root=root,
        )
        event = report["events"][0]
        self.assertEqual(
            event["consequence_evidence"]["state"],
            "ACTION_OBSERVED_EXACT_WITNESS",
        )
        self.assertEqual(event["lead_time_seconds"], 120.0)

    def test_no_action_observed_is_never_prevention_proof(self):
        p, root, reg = self.setup_bundle()
        report = m.calibrate(
            [p],
            [reg],
            [coverage()],
            [decision_receipt()],
            [case()],
            git_root=root,
        )
        consequence = report["events"][0]["consequence_evidence"]
        self.assertEqual(consequence["state"], "NO_ACTION_OBSERVED")
        self.assertFalse(consequence["prevention_evidence"])
        self.assertIsNone(report["events"][0]["lead_time_seconds"])

    def setup_bundle(self, p: dict | None = None):
        p = p or plan()
        temp, root, sha, committed_at = git_repo_with_plan(p)
        self.addCleanup(temp.cleanup)
        return p, root, registration(p, sha, committed_at)

    def test_universal_emitter_and_calibration_consumer_are_wire_compatible(self):
        p, root, reg = self.setup_bundle()
        project_receipt = {
            "schema_version": 1,
            "kind": federation.PROJECT_RECEIPT_KIND,
            "authority": federation.EVIDENCE_ONLY,
            "project": {"id": "newsletter", "repository": "FCMO-AI/FCMO-AI-Newsletter"},
            "observed_at": GATE_TIME,
            "scope": {
                "source_sha": "abc123",
                "gate_scope": "candidate_native_editions",
            },
            "evidence": [
                {
                    "id": "candidate_ready",
                    "status": "PASS",
                    "causal_root": "newsletter:candidate-ready",
                    "observed_at": GATE_TIME,
                }
            ],
            "local_decisions": [],
        }
        proofspec = {
            "schema_version": 2,
            "mission": {
                "objective": "Exercise the universal decision-receipt wire contract.",
                "context": {
                    "project_id": "newsletter",
                    "repository": "FCMO-AI/FCMO-AI-Newsletter",
                    "gate_scope": "candidate_native_editions",
                },
            },
            "claims": [],
            "gates": [
                {
                    "id": "candidate_may_enter_deploy",
                    "action": "Represent fixture candidate as admitted",
                    "behavior": "block_unless_valid",
                    "rule": {"all": ["candidate_ready"]},
                }
            ],
        }
        evaluated = federation.evaluate_project(
            proofspec,
            project_receipt,
            datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc),
            root,
        )
        emitted = evaluated["decision_receipt"]
        emitted_digest = evaluated["decision_receipt_digest"]

        c = case(digest=emitted_digest)
        c["gate"]["provenance"]["proofspec_digest"] = evaluated["proofspec_digest"]
        c["gate"]["provenance"]["effective_evidence_digest"] = (
            "sha256:" + evaluated["effective_evidence_digest"]
        )
        frame = coverage([emitted_digest])
        # Footnote: this test deliberately avoids hand-authored execution hashes.
        # The universal evaluator produces the bytes and calibration consumes those
        # exact bytes, proving the two halves share one executable wire contract.
        report = m.calibrate([p], [reg], [frame], [emitted], [c], git_root=root)
        self.assertEqual(report["episode_counts"]["TRUE_ALLOW"], 1)
        self.assertEqual(report["specificity"]["rate"], 1.0)

    def test_complete_source_enumerated_true_allow_scores(self):
        p, root, reg = self.setup_bundle()
        report = m.calibrate([p], [reg], [coverage()], [decision_receipt()], [case()], git_root=root)
        self.assertEqual(report["complete_coverage_frame_count"], 1)
        self.assertEqual(report["episode_counts"]["TRUE_ALLOW"], 1)
        self.assertEqual(report["specificity"]["rate"], 1.0)

    def test_omitted_enumerated_receipt_withholds_whole_denominator(self):
        p, root, reg = self.setup_bundle()
        # Footnote: D2 is independently enumerated by the source but intentionally
        # omitted from cases. A flattering D1-only sample must not score.
        report = m.calibrate([p], [reg], [coverage([D1, D2])], [decision_receipt()], [case()], git_root=root)
        event = report["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("INCOMPLETE_SOURCE_ENUMERATED_DENOMINATOR", event["scoreability_reasons"])
        self.assertIsNone(report["specificity"]["rate"])
        self.assertEqual(report["coverage"][0]["missing_receipt_digests"], [D2])

    def test_submitted_event_absent_from_source_frame_is_unscorable(self):
        p, root, reg = self.setup_bundle()
        report = m.calibrate([p], [reg], [coverage([D2])], [decision_receipt()], [case(digest=D1)], git_root=root)
        event = report["events"][0]
        self.assertIn("EVENT_ABSENT_FROM_COVERAGE_FRAME", event["scoreability_reasons"])
        self.assertEqual(event["classification"], "UNSCORABLE")

    def test_missing_coverage_frame_cannot_manufacture_rate(self):
        p, root, reg = self.setup_bundle()
        report = m.calibrate([p], [reg], [], [decision_receipt()], [case()], git_root=root)
        self.assertIn(
            "NO_SOURCE_ENUMERATED_COVERAGE_FRAME",
            report["events"][0]["scoreability_reasons"],
        )
        self.assertIsNone(report["specificity"]["rate"])

    def test_executed_case_without_exact_decision_bytes_is_unscorable(self):
        p, root, reg = self.setup_bundle()
        report = m.calibrate([p], [reg], [coverage()], [], [case()], git_root=root)
        event = report["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("DECISION_RECEIPT_BYTES_UNAVAILABLE", event["scoreability_reasons"])
        self.assertIsNone(report["specificity"]["rate"])

    def test_case_cannot_disagree_with_supplied_decision_receipt(self):
        p, root, reg = self.setup_bundle()
        bad = case()
        bad["gate"]["provenance"]["proofspec_digest"] = "sha256:" + "f" * 64
        # Footnote: supplying real receipt bytes is not decorative. The case cannot
        # rewrite their contract/evidence identity while keeping the receipt digest.
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.calibrate([p], [reg], [coverage()], [decision_receipt()], [bad], git_root=root)

    def test_pooled_rate_cannot_hide_unrepresented_registered_gate(self):
        p = plan()
        p["registered_gates"].append(
            {
                "project_id": "newsletter",
                "repository": "FCMO-AI/FCMO-AI-Newsletter",
                "gate_id": "represent_live_production_healthy",
            }
        )
        p, root, reg = self.setup_bundle(p)
        c = case()
        c["enrollment"]["plan_digest"] = m.v5.canonical_digest(p)

        report = m.calibrate(
            [p],
            [reg],
            [coverage()],
            [decision_receipt()],
            [c],
            git_root=root,
        )

        # Footnote: the observed deploy gate is a perfect true-allow, but the second
        # preregistered gate has no source-enumerated frame at all. The diagnostic
        # micro aggregate may show 1.0, but the headline rate is withheld because
        # "zero events" has not actually been distinguished from "never looked".
        self.assertIsNone(report["specificity"]["rate"])
        self.assertEqual(report["observed_micro_aggregate"]["specificity"]["rate"], 1.0)
        self.assertEqual(report["registered_gate_count"], 2)
        self.assertEqual(report["registered_coverage_frame_count"], 1)
        self.assertEqual(report["represented_scored_gate_count"], 1)
        self.assertEqual(
            report["registered_gate_coverage_state"],
            "MISSING_REGISTERED_COVERAGE_FRAMES",
        )
        self.assertEqual(
            report["specificity"]["withheld_reason"],
            "MISSING_REGISTERED_COVERAGE_FRAME",
        )
        missing = [
            item
            for item in report["gate_strata"]
            if item["gate_id"] == "represent_live_production_healthy"
        ][0]
        self.assertEqual(missing["state"], "NO_SCORED_DECISION_EVENTS")
        self.assertIsNone(missing["specificity"]["rate"])

    def test_explicit_zero_event_frame_distinguishes_no_events_from_no_observation(self):
        p = plan()
        p["registered_gates"].append(
            {
                "project_id": "newsletter",
                "repository": "FCMO-AI/FCMO-AI-Newsletter",
                "gate_id": "represent_live_production_healthy",
            }
        )
        p, root, reg = self.setup_bundle(p)
        c = case()
        c["enrollment"]["plan_digest"] = m.v5.canonical_digest(p)
        empty_second = coverage(
            [],
            gate_id="represent_live_production_healthy",
            coverage_id="newsletter-live-health-window-001",
        )

        report = m.calibrate(
            [p],
            [reg],
            [coverage(), empty_second],
            [decision_receipt()],
            [c],
            git_root=root,
        )

        # Footnote: an empty source-enumerated frame is positive evidence that the
        # source observed zero qualifying events in its stated window. It is not the
        # same thing as omitting the gate from observation.
        self.assertEqual(report["registered_coverage_frame_count"], 2)
        self.assertEqual(report["specificity"]["rate"], 1.0)
        self.assertEqual(
            report["registered_gate_coverage_state"],
            "COMPLETE_ENUMERATION_WITH_UNSCORED_REGISTERED_GATES",
        )

    def test_same_gate_cannot_inherit_accuracy_across_proofspec_revisions(self):
        p, root, reg = self.setup_bundle()
        first_receipt = decision_receipt()
        second_receipt = copy.deepcopy(first_receipt)
        second_receipt["proofspec_digest"] = "sha256:" + "9" * 64
        second_receipt["proof_report_digest"] = "sha256:" + "8" * 64
        second_digest = m.v5.canonical_digest(second_receipt)

        first_case = case(case_id="contract-v1", episode_id="contract-v1")
        second_case = case(
            digest=second_digest,
            case_id="contract-v2",
            episode_id="contract-v2",
        )
        second_case["gate"]["provenance"]["proofspec_digest"] = second_receipt["proofspec_digest"]

        report = m.calibrate(
            [p],
            [reg],
            [coverage([D1, second_digest])],
            [first_receipt, second_receipt],
            [first_case, second_case],
            git_root=root,
        )
        # Footnote: both contract revisions happen to be true-allows in this fixture.
        # The diagnostic mixture can say so, but a new proof contract must earn its
        # own calibration rather than inherit the old revision's headline reputation.
        self.assertEqual(report["observed_micro_aggregate"]["specificity"]["rate"], 1.0)
        self.assertIsNone(report["specificity"]["rate"])
        self.assertEqual(
            report["specificity"]["withheld_reason"],
            "MIXED_PROOFSPEC_REVISIONS_WITHIN_REGISTERED_GATE",
        )
        self.assertEqual(
            report["gate_strata"][0]["proofspec_revision_count"],
            2,
        )

    def test_unequal_right_edge_horizons_withhold_cross_gate_headline_rate(self):
        p = plan()
        p["registered_gates"].append(
            {
                "project_id": "newsletter",
                "repository": "FCMO-AI/FCMO-AI-Newsletter",
                "gate_id": "represent_live_production_healthy",
            }
        )
        p, root, reg = self.setup_bundle(p)
        c = case()
        c["enrollment"]["plan_digest"] = m.v5.canonical_digest(p)
        earlier_second = coverage(
            [],
            gate_id="represent_live_production_healthy",
            coverage_id="newsletter-live-health-window-early",
            observed_through="2026-09-18T06:09:00Z",
        )
        report = m.calibrate(
            [p],
            [reg],
            [coverage(), earlier_second],
            [decision_receipt()],
            [c],
            git_root=root,
        )
        # Footnote: both gates are explicitly enumerated, but one stops a minute
        # earlier. The sampled true-allow remains visible diagnostically while the
        # cross-gate headline is withheld to prevent selective right truncation.
        self.assertIsNone(report["specificity"]["rate"])
        self.assertEqual(
            report["specificity"]["withheld_reason"],
            "INCONSISTENT_PLAN_COVERAGE_HORIZONS",
        )
        self.assertEqual(
            report["inconsistent_coverage_horizon_plans"],
            [PLAN_ID],
        )
        self.assertEqual(report["observed_micro_aggregate"]["specificity"]["rate"], 1.0)

    def test_same_executed_receipt_cannot_be_counted_twice_via_case_or_episode_ids(self):
        p, root, reg = self.setup_bundle()
        first = case(case_id="receipt-once", episode_id="episode-a")
        duplicate = case(case_id="receipt-twice", episode_id="episode-b")
        # Footnote: both cases cite the same exact source-enumerated decision bytes.
        # Different analyst labels must not turn one real decision into two successes.
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.calibrate(
                [p],
                [reg],
                [coverage()],
                [decision_receipt()],
                [first, duplicate],
                git_root=root,
            )

    def test_real_receipt_cannot_be_relabelled_as_another_project(self):
        p, root, reg = self.setup_bundle()
        c = case()
        c["project"]["id"] = "blm"
        c["project"]["repository"] = "Magyarmex/BLM"
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.calibrate([p], [reg], [coverage()], [decision_receipt()], [c], git_root=root)

    def test_real_receipt_cannot_be_relabelled_as_another_subject(self):
        p, root, reg = self.setup_bundle()
        c = case()
        c["subject"]["gate_scope"] = "different-candidate"
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.calibrate([p], [reg], [coverage()], [decision_receipt()], [c], git_root=root)

    def test_partial_subject_overlap_is_still_underbound(self):
        p, root, reg = self.setup_bundle()
        receipt_bytes = decision_receipt()
        del receipt_bytes["context"]["source_sha"]
        digest = m.v5.canonical_digest(receipt_bytes)
        c = case(digest=digest)
        frame = coverage([digest])
        report = m.calibrate(
            [p], [reg], [frame], [receipt_bytes], [c], git_root=root
        )
        # Footnote: gate_scope still overlaps, but that generic overlap cannot stand
        # in for the missing concrete source identity.
        self.assertEqual(report["events"][0]["classification"], "UNSCORABLE")
        self.assertIn(
            "DECISION_SUBJECT_UNDERBOUND",
            report["events"][0]["scoreability_reasons"],
        )

    def test_receipt_without_any_subject_identity_overlap_is_unscorable(self):
        p, root, reg = self.setup_bundle()
        receipt_bytes = decision_receipt()
        receipt_bytes["context"] = {
            "project_id": "newsletter",
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "environment": "production",
        }
        digest = m.v5.canonical_digest(receipt_bytes)
        c = case(digest=digest)
        frame = coverage([digest])
        report = m.calibrate([p], [reg], [frame], [receipt_bytes], [c], git_root=root)
        self.assertEqual(report["events"][0]["classification"], "UNSCORABLE")
        self.assertIn(
            "DECISION_SUBJECT_UNDERBOUND",
            report["events"][0]["scoreability_reasons"],
        )

    def test_source_snapshot_digest_must_rehash_exact_snapshot_bytes(self):
        p, root, reg = self.setup_bundle()
        c = coverage()
        c["enumeration"]["source_snapshot"]["evidence_refs"].append(
            "tampered-after-digest"
        )
        # Footnote: the frame cannot retain an old digest after its claimed source
        # snapshot changes. Hash-shaped provenance without byte verification was the
        # precise denominator-laundering gap closed by v0.3i.
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.index_coverage([c], {PLAN_ID: p}, {PLAN_ID: reg})

    def test_source_snapshot_cannot_enumerate_different_receipts_than_frame(self):
        p, root, reg = self.setup_bundle()
        c = coverage([D1])
        c["enumeration"]["source_snapshot"]["decision_receipt_digests"] = [D2]
        c["enumeration"]["source_snapshot"]["source_event_count"] = 1
        c["enumeration"]["source_snapshot_digest"] = m.v5.canonical_digest(
            c["enumeration"]["source_snapshot"]
        )
        # Footnote: even a self-consistent rehashed snapshot cannot certify a frame
        # containing a different denominator.
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.index_coverage([c], {PLAN_ID: p}, {PLAN_ID: reg})

    def test_source_snapshot_count_must_match_enumerated_receipts(self):
        p, _, reg = self.setup_bundle()
        c = coverage([D1, D2])
        c["enumeration"]["source_event_count"] = 1
        # Footnote: a byte-addressed snapshot with a contradictory declared event
        # count is not a trustworthy denominator frame and must fail hard.
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.index_coverage([c], {PLAN_ID: p}, {PLAN_ID: reg})

    def test_coverage_enumerator_must_be_independent_of_spine(self):
        p, _, reg = self.setup_bundle()
        c = coverage()
        c["enumeration"]["relation_to_spine"] = "DERIVED_FROM_SPINE"
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.index_coverage([c], {PLAN_ID: p}, {PLAN_ID: reg})

    def test_first_coverage_window_cannot_start_after_plan_registration(self):
        p, _, reg = self.setup_bundle()
        c = coverage()
        c["observed_from"] = "2026-09-18T05:55:00Z"
        with self.assertRaises(m.v5.v4.CalibrationError):
            m.index_coverage([c], {PLAN_ID: p}, {PLAN_ID: reg})


if __name__ == "__main__":
    unittest.main(verbosity=2)
