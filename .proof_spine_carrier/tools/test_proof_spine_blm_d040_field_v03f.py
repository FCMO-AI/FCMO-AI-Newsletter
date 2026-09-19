#!/usr/bin/env python3
"""Field regression for BLM's falsified structural OPEN and corrected coherent cut."""
from __future__ import annotations
import importlib.util
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
assert SPEC.loader
SPEC.loader.exec_module(m)
PROOFSPEC = ROOT / "commons/experiments/2026-09-18_FCMO_PROOF_SPINE_BLM_D040_PROOFSPEC_v0.3f.json"
RECEIPT = ROOT / "commons/experiments/2026-09-18_FCMO_PROOF_SPINE_BLM_D040_FIELD_RECEIPT_v0.3f.json"
EXPECTED_RECEIPT_DIGEST = "3331ceb3464f1553f9dd1e324885d0d10d4538bcef59f0fa2b56017adc9cc2bd"


class BlmD040CoherentCutFieldTests(unittest.TestCase):
    def evaluate(self):
        spec = json.loads(PROOFSPEC.read_text(encoding="utf-8"))
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        return m.evaluate_project(spec, receipt, datetime.fromisoformat("2026-09-18T05:01:00+00:00"), ROOT)

    def test_exact_corrected_receipt_closes_stale_primary(self):
        report = self.evaluate()
        self.assertEqual(report["project_receipt_digest"], EXPECTED_RECEIPT_DIGEST)
        self.assertEqual(report["proof_report"]["evidence"]["d040_queue_execution_contract_valid"]["state"], "VALID")
        self.assertEqual(report["proof_report"]["evidence"]["d040_primary_reconciliation_clear"]["state"], "INVALID")
        self.assertEqual(report["proof_report"]["gates"]["shadow_admit_blm_primary_execution"]["state"], "CLOSED")

    def test_local_project_decision_is_deny_not_spine_authored(self):
        report = self.evaluate()
        decision = report["local_decisions"][0]
        self.assertEqual(decision["id"], "scheduler_may_execute_primary")
        self.assertEqual(decision["state"], "DENY")
        self.assertIn("reconciliation receipt", decision["basis"])

    def test_reviewed_cut_contains_both_distinct_measurement_surfaces(self):
        report = self.evaluate()
        cut = report["decision_cuts"][0]
        self.assertEqual(
            cut["required_evidence"],
            ["d040_queue_execution_contract_valid", "d040_primary_reconciliation_clear"],
        )
        self.assertTrue(cut["freshness_bound"])
        self.assertEqual(cut["gate_id"], "shadow_admit_blm_primary_execution")


if __name__ == "__main__":
    unittest.main()
