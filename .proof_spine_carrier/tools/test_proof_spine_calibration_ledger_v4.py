#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("calibration_v4", HERE/"proof_spine_calibration_ledger_v4.py")
m=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(m)
SUBJECT={"source_sha":"abc123","obligation_id":"FCMO-TEST","gate_scope":"candidate_native_editions"}

def provenance(state="EXECUTED", roots=None):
    p={"state":state,"mechanism_id":"proof-spine-v0.3e","evaluated_at":"2026-09-16T19:22:02.358706Z","evidence_refs":["receipt:source"],"measurement_roots":roots or ["observer:spine-scan"]}
    if state=="EXECUTED":
        p.update({"proofspec_digest":"sha256:"+"1"*64,"effective_evidence_digest":"sha256:"+"2"*64,"decision_receipt_digest":"sha256:"+"3"*64,"decision_receipt_kind":"FCMO_PROOF_SPINE_DECISION_RECEIPT"})
    return p

def case(case_id="x",episode="e",decision="CLOSED",actual="SHOULD_BLOCK",*,pstate="EXECUTED",relation="INDEPENDENT_OF_SPINE",occurred=True,gate_roots=None,adjudication_roots=None):
    action={"occurred":occurred}
    if occurred: action.update({"kind":"DEPLOY","observed_at":"2026-09-16T21:21:42Z","subject":copy.deepcopy(SUBJECT)})
    return {"schema_version":4,"kind":m.KIND,"authority":m.AUTHORITY,"case_id":case_id,"episode_id":episode,"subject":copy.deepcopy(SUBJECT),"project":{"id":"newsletter","repository":"FCMO-AI/FCMO-AI-Newsletter"},"gate":{"id":"candidate_may_enter_deploy","decision":decision,"reason":"INVALID" if decision=="CLOSED" else "VALID","observed_at":"2026-09-16T19:22:02.358706Z","provenance":provenance(pstate,gate_roots)},"action":action,"adjudication":{"source_authority":m.PROJECT_LOCAL,"state":actual,"relation_to_spine":relation,"observed_at":"2026-09-16T21:23:14Z","subject":copy.deepcopy(SUBJECT),"basis":"Project-local evidence","mechanism":{"id":"local-oracle","origin":"PREEXISTING_PROJECT_LOCAL" if relation=="INDEPENDENT_OF_SPINE" else "SPINE_DERIVED","established_at":"2026-09-16T19:00:00Z","evidence_refs":["workflow:local-oracle"],"measurement_roots":adjudication_roots or ["oracle:independent-postcondition"]}},"evidence_refs":["run:1"]}

class T(unittest.TestCase):
    def test_disjoint_executed_measurements_score(self): self.assertEqual(m.classify(case())["classification"],"TRUE_BLOCK")
    def test_same_measurement_path_is_unscorable(self):
        e=m.classify(case(gate_roots=["oracle:shared"],adjudication_roots=["oracle:shared"]))
        self.assertEqual(e["classification"],"UNSCORABLE"); self.assertIn("ADJUDICATION_REUSES_GATE_MEASUREMENT",e["scoreability_reasons"])
    def test_same_measurement_cannot_manufacture_specificity(self):
        r=m.calibrate([case("a","a",decision="OPEN",actual="SHOULD_ALLOW",gate_roots=["oracle:shared"],adjudication_roots=["oracle:shared"])])
        self.assertEqual(r["scored_episode_count"],0); self.assertIsNone(r["specificity"]["rate"])
    def test_distinct_measurement_true_allow_creates_specificity(self):
        r=m.calibrate([case("a","a",decision="OPEN",actual="SHOULD_ALLOW",gate_roots=["observer:queue"],adjudication_roots=["oracle:postcondition"])])
        self.assertEqual(r["episode_counts"]["TRUE_ALLOW"],1); self.assertEqual(r["specificity"]["rate"],1.0)
    def test_derived_gate_is_unscorable(self): self.assertIn("GATE_NOT_EXECUTED",m.classify(case(pstate="DERIVED"))["scoreability_reasons"])
    def test_missing_gate_roots_rejected(self):
        c=case(); del c["gate"]["provenance"]["measurement_roots"]
        with self.assertRaises(m.CalibrationError): m.classify(c)
    def test_missing_adjudication_roots_rejected(self):
        c=case(); del c["adjudication"]["mechanism"]["measurement_roots"]
        with self.assertRaises(m.CalibrationError): m.classify(c)
    def test_execution_digest_required(self):
        c=case(); del c["gate"]["provenance"]["effective_evidence_digest"]
        with self.assertRaises(m.CalibrationError): m.classify(c)
    def test_independent_of_spine_required(self): self.assertIn("ADJUDICATION_NOT_INDEPENDENT_OF_SPINE",m.classify(case(relation="DERIVED_FROM_SPINE"))["scoreability_reasons"])
    def test_zero_executed_keeps_rates_null(self):
        r=m.calibrate([case("x","x",pstate="DERIVED")]); self.assertIsNone(r["sensitivity"]["rate"]); self.assertIsNone(r["specificity"]["rate"])
    def test_retry_dedupe(self):
        a=case("first","same"); b=case("retry","same"); b["gate"]["observed_at"]="2026-09-16T20:00:00Z"; b["gate"]["provenance"]["evaluated_at"]="2026-09-16T20:00:00Z"
        r=m.calibrate([a,b]); self.assertEqual(r["scored_episode_count"],1); self.assertEqual(r["event_counts"]["TRUE_BLOCK"],2)

if __name__=="__main__": unittest.main()
