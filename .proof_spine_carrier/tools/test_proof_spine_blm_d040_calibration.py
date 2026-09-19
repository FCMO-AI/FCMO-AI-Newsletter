#!/usr/bin/env python3
"""Regression for the BLM stale-primary falsification in calibration v4."""
from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("calibration_v4", HERE / "proof_spine_calibration_ledger_v4.py")
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)
CASES = ROOT / "commons/experiments/2026-09-18_FCMO_PROOF_SPINE_CALIBRATION_CASES_v0.3f.json"

class BlmCalibrationFalsificationTests(unittest.TestCase):
    def test_open_should_block_relation_is_preserved_even_without_action(self):
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        case = next(c for c in cases if c["case_id"] == "blm-d040-stale-primary-structural-open-2026-09-18")
        event = m.classify(case)
        self.assertFalse(event["action_occurred"])
        self.assertEqual(event["gate_decision"], "OPEN")
        self.assertEqual(event["actual"], "SHOULD_BLOCK")
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertEqual(event["scoreability_reasons"], ["GATE_NOT_EXECUTED"])
        self.assertEqual(event["measurement_overlap"], [])

    def test_unscored_falsification_does_not_pollute_accuracy_denominators(self):
        report = m.calibrate(json.loads(CASES.read_text(encoding="utf-8")))
        self.assertEqual(report["case_count"], 4)
        self.assertEqual(report["scored_episode_count"], 0)
        self.assertEqual(report["event_counts"]["UNSCORABLE"], 4)
        self.assertIsNone(report["sensitivity"]["rate"])
        self.assertIsNone(report["specificity"]["rate"])


if __name__ == "__main__":
    unittest.main()
