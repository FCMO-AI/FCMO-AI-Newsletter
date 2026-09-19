#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("calibration_v5", HERE / "proof_spine_calibration_ledger_v5.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(m)

PLAN_PATH = "commons/experiments/FCMO_PROOF_SPINE_CALIBRATION_PLAN_TEST.json"
PLAN_ID = "fcmo-proof-spine-test-plan"
PLAN_TIME = "2026-09-18T05:50:00+00:00"
GATE_TIME = "2026-09-18T06:00:00Z"


def plan(*, outcome_blind: bool = True) -> dict:
    return {
        "schema_version": 1,
        "kind": m.PLAN_KIND,
        "authority": m.PLAN_AUTHORITY,
        "plan_id": PLAN_ID,
        "authored_at": "2026-09-18T05:45:00Z",
        "sampling_mode": m.SAMPLING_MODE,
        "outcome_blind": outcome_blind,
        "registered_gates": [
            {
                "project_id": "newsletter",
                "repository": "FCMO-AI/FCMO-AI-Newsletter",
                "gate_id": "candidate_may_enter_deploy",
            }
        ],
        "notes": ["Enroll all future qualifying events, not outcome-selected examples."],
    }


def git_repo_with_plan(p: dict, *, commit_time: str = PLAN_TIME) -> tuple[tempfile.TemporaryDirectory, Path, str, str]:
    temp = tempfile.TemporaryDirectory(prefix="proof-spine-plan-git-")
    root = Path(temp.name)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "FCMO Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    target = root / PLAN_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps([p], ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", PLAN_PATH], check=True)
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_time
    env["GIT_COMMITTER_DATE"] = commit_time
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "Register calibration plan"], check=True, env=env)
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    committed_at = subprocess.check_output(["git", "-C", str(root), "show", "-s", "--format=%cI", sha], text=True).strip()
    return temp, root, sha, committed_at


def registration(p: dict, sha: str, committed_at: str) -> dict:
    return {
        "schema_version": 1,
        "kind": m.REGISTRATION_KIND,
        "authority": m.PLAN_AUTHORITY,
        "plan_id": PLAN_ID,
        "plan_digest": m.canonical_digest(p),
        "repository": "FCMO-AI/FCMO-Agent-Hub",
        "path": PLAN_PATH,
        "commit_sha": sha,
        "committed_at": committed_at,
        "evidence_refs": [f"git-commit:{sha}", f"git-path:{PLAN_PATH}"],
    }


def case(
    *,
    mode: str = "PROSPECTIVE",
    gate_time: str = GATE_TIME,
    decision: str = "OPEN",
    actual: str = "SHOULD_ALLOW",
    gate_id: str = "candidate_may_enter_deploy",
    pstate: str = "EXECUTED",
    shared_root: bool = False,
    case_id: str = "case-1",
    episode_id: str = "episode-1",
) -> dict:
    subject = {"source_sha": "abc123", "gate_scope": "candidate_native_editions"}
    gate_roots = ["spine:gate-measurement"]
    adj_roots = gate_roots if shared_root else ["project:independent-postcondition"]
    return {
        "schema_version": 4,
        "kind": "FCMO_PROOF_SPINE_CALIBRATION_CASE",
        "authority": "EVIDENCE_ONLY",
        "case_id": case_id,
        "episode_id": episode_id,
        "subject": subject,
        "project": {"id": "newsletter", "repository": "FCMO-AI/FCMO-AI-Newsletter"},
        "gate": {
            "id": gate_id,
            "decision": decision,
            "reason": "VALID" if decision == "OPEN" else "INVALID",
            "observed_at": gate_time,
            "provenance": {
                "state": pstate,
                "mechanism_id": "proof-spine-test",
                "evaluated_at": gate_time,
                "evidence_refs": ["receipt:test"],
                "measurement_roots": gate_roots,
                **({
                    "proofspec_digest": "sha256:" + "1" * 64,
                    "effective_evidence_digest": "sha256:" + "2" * 64,
                    "decision_receipt_digest": "sha256:" + "3" * 64,
                    "decision_receipt_kind": "FCMO_PROOF_SPINE_DECISION_RECEIPT",
                } if pstate == "EXECUTED" else {}),
            },
        },
        "action": {"occurred": False},
        "adjudication": {
            "source_authority": "PROJECT_LOCAL",
            "state": actual,
            "relation_to_spine": "INDEPENDENT_OF_SPINE",
            "observed_at": "2026-09-18T06:05:00Z",
            "subject": subject,
            "basis": "Independent project-local outcome",
            "mechanism": {
                "id": "project-local-oracle",
                "origin": "PREEXISTING_PROJECT_LOCAL",
                "established_at": "2026-09-18T05:00:00Z",
                "evidence_refs": ["workflow:project-local-oracle"],
                "measurement_roots": adj_roots,
            },
        },
        "evidence_refs": ["run:test"],
        "enrollment": {"mode": mode, "plan_id": PLAN_ID, "plan_digest": m.canonical_digest(plan())},
    }


class CalibrationV5Tests(unittest.TestCase):
    def setup_bundle(self, *, commit_time: str = PLAN_TIME, p: dict | None = None):
        p = p or plan()
        temp, root, sha, committed_at = git_repo_with_plan(p, commit_time=commit_time)
        self.addCleanup(temp.cleanup)
        return p, root, registration(p, sha, committed_at)

    def test_git_verified_prospective_true_allow_scores(self) -> None:
        p, root, reg = self.setup_bundle()
        report = m.calibrate([p], [reg], [case()], git_root=root)
        self.assertEqual(report["git_verified_plan_count"], 1)
        self.assertEqual(report["episode_counts"]["TRUE_ALLOW"], 1)
        self.assertEqual(report["specificity"]["rate"], 1.0)

    def test_without_git_verification_cannot_score(self) -> None:
        p, _, reg = self.setup_bundle()
        event = m.calibrate([p], [reg], [case()])["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("PLAN_PROVENANCE_NOT_GIT_VERIFIED", event["scoreability_reasons"])

    def test_retrospective_case_remains_unscorable_even_with_verified_plan(self) -> None:
        p, root, reg = self.setup_bundle()
        event = m.calibrate([p], [reg], [case(mode="RETROSPECTIVE")], git_root=root)["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("RETROSPECTIVE_ENROLLMENT", event["scoreability_reasons"])

    def test_backdated_json_cannot_rescue_plan_committed_after_gate(self) -> None:
        p, root, reg = self.setup_bundle(commit_time="2026-09-18T06:10:00+00:00")
        event = m.calibrate([p], [reg], [case(gate_time="2026-09-18T06:00:00Z")], git_root=root)["events"][0]
        self.assertIn("PLAN_POSTDATES_GATE", event["scoreability_reasons"])
        self.assertEqual(event["classification"], "UNSCORABLE")

    def test_unregistered_gate_is_unscorable(self) -> None:
        p, root, reg = self.setup_bundle()
        event = m.calibrate([p], [reg], [case(gate_id="another_gate")], git_root=root)["events"][0]
        self.assertIn("GATE_NOT_REGISTERED_IN_PLAN", event["scoreability_reasons"])

    def test_registration_timestamp_must_match_git(self) -> None:
        p, root, reg = self.setup_bundle()
        bad = copy.deepcopy(reg)
        bad["committed_at"] = "2026-09-18T05:49:00Z"
        with self.assertRaises(m.PlanVerificationError):
            m.calibrate([p], [bad], [case()], git_root=root)

    def test_plan_digest_tampering_is_hard_error(self) -> None:
        p, root, reg = self.setup_bundle()
        bad = copy.deepcopy(reg)
        bad["plan_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(m.v4.CalibrationError):
            m.calibrate([p], [bad], [case()], git_root=root)

    def test_outcome_blind_is_mandatory(self) -> None:
        p = plan(outcome_blind=False)
        with self.assertRaises(m.v4.CalibrationError):
            m.validate_plan(p)

    def test_v4_measurement_independence_still_applies(self) -> None:
        p, root, reg = self.setup_bundle()
        event = m.calibrate([p], [reg], [case(shared_root=True)], git_root=root)["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("ADJUDICATION_REUSES_GATE_MEASUREMENT", event["scoreability_reasons"])

    def test_v4_executed_gate_requirement_still_applies(self) -> None:
        p, root, reg = self.setup_bundle()
        event = m.calibrate([p], [reg], [case(pstate="RECONSTRUCTED")], git_root=root)["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("GATE_NOT_EXECUTED", event["scoreability_reasons"])

    def test_retry_dedupe_survives_preregistration_layer(self) -> None:
        p, root, reg = self.setup_bundle()
        a = case(case_id="first", episode_id="same")
        b = case(case_id="retry", episode_id="same", gate_time="2026-09-18T06:01:00Z")
        b["adjudication"]["observed_at"] = "2026-09-18T06:06:00Z"
        report = m.calibrate([p], [reg], [a, b], git_root=root)
        self.assertEqual(report["event_counts"]["TRUE_ALLOW"], 2)
        self.assertEqual(report["scored_episode_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
