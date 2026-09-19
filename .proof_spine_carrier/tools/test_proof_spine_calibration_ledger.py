#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("calibration", HERE / "proof_spine_calibration_ledger.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)


def case(case_id: str, episode: str, decision: str, actual: str, action_time: str = "2026-09-16T21:21:42Z"):
    return {"schema_version":1,"kind":m.KIND,"authority":m.AUTHORITY,"case_id":case_id,"episode_id":episode,"project":{"id":"newsletter","repository":"FCMO-AI/FCMO-AI-Newsletter"},"gate":{"id":"candidate_may_enter_deploy","decision":decision,"reason":"INVALID" if decision=="CLOSED" else "VALID","observed_at":"2026-09-16T19:22:02.358706Z"},"action":{"occurred":True,"kind":"DEPLOY","observed_at":action_time},"adjudication":{"source_authority":m.PROJECT_LOCAL,"state":actual,"basis":"Newsletter-local release/health evidence"},"evidence_refs":["run:35140061610","run:35151946023"]}


class CalibrationTests(unittest.TestCase):
    def test_confusion_matrix_labels(self):
        self.assertEqual(m.classify(case("tp","a","CLOSED","SHOULD_BLOCK"))["classification"],"TRUE_POSITIVE")
        self.assertEqual(m.classify(case("tn","b","OPEN","SHOULD_ALLOW"))["classification"],"TRUE_NEGATIVE")
        self.assertEqual(m.classify(case("fp","c","CLOSED","SHOULD_ALLOW"))["classification"],"FALSE_BLOCK")
        self.assertEqual(m.classify(case("fn","d","OPEN","SHOULD_BLOCK"))["classification"],"MISS")
    def test_no_action_is_unscorable(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK"); c["action"]={"occurred":False}; self.assertEqual(m.classify(c)["classification"],"UNSCORABLE")
    def test_unknown_actual_is_unscorable(self):
        self.assertEqual(m.classify(case("x","e","CLOSED","UNKNOWN"))["classification"],"UNSCORABLE")
    def test_project_local_adjudication_required(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK"); c["adjudication"]["source_authority"]="PROOF_SPINE"
        with self.assertRaises(m.CalibrationError): m.classify(c)
    def test_action_must_follow_gate(self):
        c=case("x","e","CLOSED","SHOULD_BLOCK","2026-09-16T19:00:00Z")
        with self.assertRaises(m.CalibrationError): m.classify(c)
    def test_retries_same_episode_do_not_inflate_headline(self):
        a=case("first","episode","CLOSED","SHOULD_BLOCK","2026-09-16T21:21:42Z"); b=case("retry","episode","CLOSED","SHOULD_BLOCK","2026-09-16T23:21:42Z")
        r=m.calibrate([a,b]); self.assertEqual(r["event_counts"]["TRUE_POSITIVE"],2); self.assertEqual(r["episode_counts"]["TRUE_POSITIVE"],1); self.assertEqual(r["scored_episode_count"],1)
    def test_zero_specificity_denominator_stays_null(self):
        r=m.calibrate([case("tp","episode","CLOSED","SHOULD_BLOCK")]); self.assertEqual(r["sensitivity"]["rate"],1.0); self.assertIsNone(r["specificity"]["rate"]); self.assertIsNone(r["false_block_rate"]["rate"])
    def test_false_block_rate_uses_negative_episodes_only(self):
        r=m.calibrate([case("tn","good-1","OPEN","SHOULD_ALLOW"),case("fp","good-2","CLOSED","SHOULD_ALLOW")]); self.assertEqual(r["false_block_rate"]["numerator"],1); self.assertEqual(r["false_block_rate"]["denominator"],2); self.assertEqual(r["false_block_rate"]["rate"],0.5)
    def test_duplicate_case_ids_rejected(self):
        c=case("dup","one","CLOSED","SHOULD_BLOCK"); d=copy.deepcopy(c); d["episode_id"]="two"
        with self.assertRaises(m.CalibrationError): m.calibrate([c,d])

if __name__=="__main__": unittest.main()
