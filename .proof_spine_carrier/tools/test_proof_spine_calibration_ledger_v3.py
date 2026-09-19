#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("calibration_v3", HERE / "proof_spine_calibration_ledger_v3.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)

SUBJECT = {"source_sha": "abc123", "obligation_id": "FCMO-TEST", "gate_scope": "candidate_native_editions"}

def provenance(state="EXECUTED"):
    p = {
        "state": state,
        "mechanism_id": "proof-spine-v0.3d",
        "evaluated_at": "2026-09-16T19:22:02.358706Z",
        "evidence_refs": ["receipt:source"],
    }
    if state == "EXECUTED":
        p.update({
            "proofspec_digest": "sha256:" + "1" * 64,
            "effective_evidence_digest": "sha256:" + "2" * 64,
            "decision_receipt_digest": "sha256:" + "3" * 64,
            "decision_receipt_kind": "FCMO_PROOF_SPINE_DECISION_RECEIPT",
        })
    return p

def case(case_id="x", episode="e", decision="CLOSED", actual="SHOULD_BLOCK", *, pstate="EXECUTED",
         relation="INDEPENDENT_OF_SPINE", occurred=True):
    action = {"occurred": occurred}
    if occurred:
        action.update({"kind": "DEPLOY", "observed_at": "2026-09-16T21:21:42Z", "subject": copy.deepcopy(SUBJECT)})
    return {
        "schema_version": 3,
        "kind": m.KIND,
        "authority": m.AUTHORITY,
        "case_id": case_id,
        "episode_id": episode,
        "subject": copy.deepcopy(SUBJECT),
        "project": {"id": "newsletter", "repository": "FCMO-AI/FCMO-AI-Newsletter"},
        "gate": {
            "id": "candidate_may_enter_deploy",
            "decision": decision,
            "reason": "INVALID" if decision == "CLOSED" else "VALID",
            "observed_at": "2026-09-16T19:22:02.358706Z",
            "provenance": provenance(pstate),
        },
        "action": action,
        "adjudication": {
            "source_authority": m.PROJECT_LOCAL,
            "state": actual,
            "relation_to_spine": relation,
            "observed_at": "2026-09-16T21:23:14Z",
            "subject": copy.deepcopy(SUBJECT),
            "basis": "Newsletter-local evidence",
            "mechanism": {
                "id": "newsletter-local-oracle",
                "origin": "PREEXISTING_PROJECT_LOCAL" if relation == "INDEPENDENT_OF_SPINE" else "SPINE_DERIVED",
                "established_at": "2026-09-16T19:00:00Z",
                "evidence_refs": ["workflow:local-oracle"],
            },
        },
        "evidence_refs": ["run:1"],
    }

class CalibrationV3Tests(unittest.TestCase):
    def test_executed_independently_adjudicated_gate_scores(self):
        self.assertEqual(m.classify(case())["classification"], "TRUE_BLOCK")

    def test_derived_gate_is_unscorable(self):
        event = m.classify(case(pstate="DERIVED"))
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("GATE_NOT_EXECUTED", event["scoreability_reasons"])

    def test_reconstructed_gate_is_unscorable(self):
        self.assertEqual(m.classify(case(pstate="RECONSTRUCTED"))["classification"], "UNSCORABLE")

    def test_derived_gate_may_not_claim_execution_digests(self):
        c = case(pstate="DERIVED")
        c["gate"]["provenance"]["decision_receipt_digest"] = "sha256:" + "3" * 64
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_executed_gate_requires_three_digests(self):
        c = case()
        del c["gate"]["provenance"]["effective_evidence_digest"]
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_executed_gate_rejects_fake_digest(self):
        c = case()
        c["gate"]["provenance"]["proofspec_digest"] = "sha256:not-a-digest"
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_gate_provenance_time_must_bind_gate_observation(self):
        c = case()
        c["gate"]["provenance"]["evaluated_at"] = "2026-09-16T19:22:03Z"
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_independent_adjudication_still_required(self):
        event = m.classify(case(relation="DERIVED_FROM_SPINE"))
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn("ADJUDICATION_NOT_INDEPENDENT", event["scoreability_reasons"])

    def test_zero_executed_cases_keep_all_accuracy_rates_null(self):
        report = m.calibrate([
            case("derived-block", "a", pstate="DERIVED"),
            case("derived-allow", "b", decision="OPEN", actual="SHOULD_ALLOW", pstate="DERIVED"),
        ])
        self.assertEqual(report["executed_gate_case_count"], 0)
        self.assertEqual(report["scored_episode_count"], 0)
        self.assertIsNone(report["sensitivity"]["rate"])
        self.assertIsNone(report["specificity"]["rate"])
        self.assertEqual(report["scoreability_counts"]["GATE_NOT_EXECUTED"], 2)

    def test_executed_true_allow_creates_specificity_denominator(self):
        report = m.calibrate([case("allow", "allow-episode", decision="OPEN", actual="SHOULD_ALLOW")])
        self.assertEqual(report["episode_counts"]["TRUE_ALLOW"], 1)
        self.assertEqual(report["specificity"]["rate"], 1.0)

    def test_retry_dedupe_still_uses_episode(self):
        a = case("first", "same")
        b = case("retry", "same")
        b["gate"]["observed_at"] = "2026-09-16T20:00:00Z"
        b["gate"]["provenance"]["evaluated_at"] = "2026-09-16T20:00:00Z"
        report = m.calibrate([a, b])
        self.assertEqual(report["scored_episode_count"], 1)
        self.assertEqual(report["event_counts"]["TRUE_BLOCK"], 2)

if __name__ == "__main__":
    unittest.main()
