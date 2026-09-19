#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

from proof_spine_action_witness import evaluate_action_witness
from proof_spine_obligation_memory import evaluate_obligation_memory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURE = ROOT / "commons" / "experiments" / "2026-09-17_FCMO_PROOF_SPINE_NEWSLETTER_TEMPORAL_FIELD_CASE_v0.3a.json"


class NewsletterTemporalFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.case = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_real_shadow_closed_before_later_pages_action(self) -> None:
        case = self.case
        witness = evaluate_action_witness(
            case["witness_contract"],
            case["proof_observation"],
            case["action_observation"],
            case["corroboration"],
        )
        expected = case["expected_witness"]
        self.assertEqual(witness["classification"], expected["classification"])
        self.assertAlmostEqual(witness["temporal_relation"]["lead_seconds"], expected["lead_seconds"], places=6)
        self.assertTrue(witness["temporal_relation"]["proof_precedes_action"])
        self.assertTrue(witness["temporal_relation"]["corroboration_follows_action"])

    def test_same_material_defect_binds_the_field_subject_across_action(self) -> None:
        witness = evaluate_action_witness(
            self.case["witness_contract"],
            self.case["proof_observation"],
            self.case["action_observation"],
            self.case["corroboration"],
        )
        self.assertEqual(witness["subject_binding"]["state"], "EXACT")
        self.assertEqual(witness["subject_binding"]["continuity"]["state"], "MATCH")

    def test_later_healthy_window_does_not_resolve_known_localization_debt(self) -> None:
        case = self.case
        memory = evaluate_obligation_memory(case["obligation_contract"], case["obligation_snapshots"])
        expected = case["expected_obligation_memory"]
        self.assertEqual(memory["summary"]["active"], expected["active"])
        self.assertEqual(memory["summary"]["resolved"], expected["resolved"])
        self.assertEqual(memory["transitions"][-1]["event"], expected["terminal_event"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
