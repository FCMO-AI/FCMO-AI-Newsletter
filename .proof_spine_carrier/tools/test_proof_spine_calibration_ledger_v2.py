#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("calibration_v2", HERE / "proof_spine_calibration_ledger_v2.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)

SUBJECT = {"source_sha":"abc123","obligation_id":"FCMO-TEST","gate_scope":"candidate_native_editions"}


def case(case_id, episode, decision, actual, *, occurred=True,
         action_time="2026-09-16T21:21:42Z", relation="INDEPENDENT_OF_SPINE",
         adjudicated_at="2026-09-16T21:23:14Z",
         mechanism_origin="PREEXISTING_PROJECT_LOCAL",
         mechanism_established_at="2026-09-16T19:00:00Z"):
    action = {"occurred": occurred}
    if occurred:
        action.update({"kind":"DEPLOY","observed_at":action_time,"subject":copy.deepcopy(SUBJECT)})
    return {
        "schema_version":2,
        "kind":m.KIND,
        "authority":m.AUTHORITY,
        "case_id":case_id,
        "episode_id":episode,
        "subject":copy.deepcopy(SUBJECT),
        "project":{"id":"newsletter","repository":"FCMO-AI/FCMO-AI-Newsletter"},
        "gate":{"id":"candidate_may_enter_deploy","decision":decision,
                "reason":"INVALID" if decision=="CLOSED" else "VALID",
                "observed_at":"2026-09-16T19:22:02.358706Z"},
        "action":action,
        "adjudication":{"source_authority":m.PROJECT_LOCAL,"state":actual,
                        "relation_to_spine":relation,"observed_at":adjudicated_at,
                        "subject":copy.deepcopy(SUBJECT),
                        "basis":"Newsletter-local evidence",
                        "mechanism":{"id":"newsletter-local-oracle","origin":mechanism_origin,
                                     "established_at":mechanism_established_at,
                                     "evidence_refs":["workflow:local-oracle"]}},
        "evidence_refs":["run:1"],
    }


class CalibrationV2Tests(unittest.TestCase):
    def test_confusion_matrix_labels(self):
        self.assertEqual(m.classify(case("tb","a","CLOSED","SHOULD_BLOCK"))["classification"],"TRUE_BLOCK")
        self.assertEqual(m.classify(case("ta","b","OPEN","SHOULD_ALLOW"))["classification"],"TRUE_ALLOW")
        self.assertEqual(m.classify(case("fb","c","CLOSED","SHOULD_ALLOW"))["classification"],"FALSE_BLOCK")
        self.assertEqual(m.classify(case("fa","d","OPEN","SHOULD_BLOCK"))["classification"],"FALSE_ALLOW")

    def test_no_action_can_still_score_decision_correctness(self):
        event=m.classify(case("x","e","CLOSED","SHOULD_BLOCK",occurred=False))
        self.assertEqual(event["classification"],"TRUE_BLOCK")
        self.assertFalse(event["action_occurred"])
        self.assertIsNone(event["lead_time_seconds"])

    def test_false_block_remains_visible_when_action_was_prevented(self):
        self.assertEqual(m.classify(case("x","e","CLOSED","SHOULD_ALLOW",occurred=False))["classification"],"FALSE_BLOCK")

    def test_unknown_actual_is_unscorable(self):
        self.assertEqual(m.classify(case("x","e","CLOSED","UNKNOWN"))["classification"],"UNSCORABLE")

    def test_spine_derived_adjudication_is_unscorable(self):
        self.assertEqual(
            m.classify(case("x","e","CLOSED","SHOULD_BLOCK",relation="DERIVED_FROM_SPINE",
                            mechanism_origin="SPINE_DERIVED"))["classification"],
            "UNSCORABLE",
        )

    def test_independent_label_cannot_override_spine_derived_mechanism(self):
        with self.assertRaises(m.CalibrationError):
            m.classify(case("x","e","CLOSED","SHOULD_BLOCK",
                            relation="INDEPENDENT_OF_SPINE", mechanism_origin="SPINE_DERIVED"))

    def test_preexisting_local_mechanism_cannot_postdate_gate(self):
        with self.assertRaises(m.CalibrationError):
            m.classify(case("x","e","CLOSED","SHOULD_BLOCK",
                            mechanism_established_at="2026-09-16T20:00:00Z"))

    def test_missing_mechanism_provenance_is_rejected(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK")
        del c["adjudication"]["mechanism"]
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_project_local_adjudication_required(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK")
        c["adjudication"]["source_authority"]="PROOF_SPINE"
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_adjudication_cannot_predate_gate(self):
        with self.assertRaises(m.CalibrationError):
            m.classify(case("x","e","CLOSED","SHOULD_BLOCK",adjudicated_at="2026-09-16T19:00:00Z"))

    def test_action_subject_must_match(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK")
        c["action"]["subject"]["source_sha"]="different"
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_adjudication_subject_must_match(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK")
        c["adjudication"]["subject"]["obligation_id"]="other"
        with self.assertRaises(m.CalibrationError):
            m.classify(c)

    def test_action_must_follow_gate(self):
        with self.assertRaises(m.CalibrationError):
            m.classify(case("x","e","CLOSED","SHOULD_BLOCK",action_time="2026-09-16T19:00:00Z"))

    def test_retry_dedupe_uses_earliest_gate_not_first_action(self):
        a=case("first","episode","CLOSED","SHOULD_BLOCK",action_time="2026-09-16T23:21:42Z")
        b=case("later-gate-earlier-action","episode","CLOSED","SHOULD_BLOCK",action_time="2026-09-16T21:21:42Z")
        b["gate"]["observed_at"]="2026-09-16T20:00:00Z"
        b["adjudication"]["observed_at"]="2026-09-16T21:23:14Z"
        r=m.calibrate([a,b])
        self.assertEqual(r["episodes"][0]["case_id"],"first")
        self.assertEqual(r["event_counts"]["TRUE_BLOCK"],2)

    def test_no_action_episode_can_be_headline_sample(self):
        r=m.calibrate([case("x","e","CLOSED","SHOULD_BLOCK",occurred=False)])
        self.assertEqual(r["scored_episode_count"],1)
        self.assertEqual(r["observed_action_count"],0)

    def test_zero_specificity_denominator_stays_null(self):
        r=m.calibrate([case("x","e","CLOSED","SHOULD_BLOCK")])
        self.assertIsNone(r["specificity"]["rate"])
        self.assertIsNone(r["false_block_rate"]["rate"])

    def test_false_block_rate_uses_allowable_episodes_only(self):
        r=m.calibrate([
            case("ta","a","OPEN","SHOULD_ALLOW"),
            case("fb","b","CLOSED","SHOULD_ALLOW",occurred=False),
        ])
        self.assertEqual(r["false_block_rate"]["rate"],0.5)

    def test_duplicate_case_ids_rejected(self):
        c=case("dup","a","CLOSED","SHOULD_BLOCK")
        d=copy.deepcopy(c)
        d["episode_id"]="b"
        with self.assertRaises(m.CalibrationError):
            m.calibrate([c,d])


if __name__=="__main__":
    unittest.main()
