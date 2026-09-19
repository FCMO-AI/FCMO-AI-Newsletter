#!/usr/bin/env python3
"""Field regression for the BLM D040 Proof Spine project receipt."""
from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)

PROOFSPEC = ROOT / "commons/experiments/2026-09-18_FCMO_PROOF_SPINE_BLM_D040_PROOFSPEC_v0.3e.json"
RECEIPT = ROOT / "commons/experiments/2026-09-18_FCMO_PROOF_SPINE_BLM_D040_FIELD_RECEIPT_v0.3e.json"
EXPECTED_RECEIPT_DIGEST = "83aaead2d80060383646005c5ccf2208fc54ef20548dd808645779e47c71ca05"


class BlmD040FieldTests(unittest.TestCase):
    def evaluate(self):
        spec = json.loads(PROOFSPEC.read_text(encoding="utf-8"))
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        now = datetime.fromisoformat("2026-09-18T04:36:00+00:00")
        return m.evaluate_project(spec, receipt, now, ROOT)

    def test_exact_field_receipt_opens_only_scheduler_admission_gate(self):
        report = self.evaluate()
        self.assertEqual(report["project_receipt_digest"], EXPECTED_RECEIPT_DIGEST)
        self.assertEqual(report["proof_report"]["summary"]["open_gates"], ["shadow_admit_blm_primary_execution"])
        self.assertEqual(report["proof_report"]["summary"]["closed_gates"], [])

    def test_local_allow_remains_narrow_and_project_owned(self):
        report = self.evaluate()
        decision = report["local_decisions"][0]
        self.assertEqual(decision["state"], "ALLOW")
        self.assertEqual(decision["id"], "scheduler_may_execute_primary")
        self.assertEqual(decision["scope_boundary"], "SCHEDULING_STRUCTURE_ONLY_NO_SCIENTIFIC_PROMOTION_NO_COMPUTE_LAUNCH")

    def test_field_contract_cannot_claim_scientific_promotion(self):
        report = self.evaluate()
        action = report["proof_report"]["gates"]["shadow_admit_blm_primary_execution"]["action"]
        self.assertIn("not scientific promotion", action)
        self.assertEqual(report["proof_report"]["evidence"]["d040_queue_execution_contract_valid"]["state"], "VALID")


if __name__ == "__main__":
    unittest.main()
