#!/usr/bin/env python3
"""Field regression for the Newsletter localization/deployment causal gap."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC_PATH = ROOT / "commons/experiments/2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_PROOFSPEC_v0.2c.json"
RECEIPT_PATH = ROOT / "commons/experiments/2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_FIELD_RECEIPT_v0.2c.json"

MODULE_SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
federation = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = federation
MODULE_SPEC.loader.exec_module(federation)

NOW = datetime(2026, 9, 16, 1, 54, 3, tzinfo=timezone.utc)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evidence(receipt: dict, eid: str) -> dict:
    return next(item for item in receipt["evidence"] if item["id"] == eid)


class NewsletterLocalizationFieldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = load(SPEC_PATH)
        self.receipt = load(RECEIPT_PATH)

    def evaluate(self, receipt: dict | None = None) -> dict:
        return federation.evaluate_project(self.spec, receipt or self.receipt, NOW, ROOT)["proof_report"]

    def test_real_deploy_success_cannot_override_failed_localization_prerequisite(self) -> None:
        report = self.evaluate()
        gate = report["gates"]["candidate_may_enter_deploy"]
        self.assertEqual(report["evidence"]["candidate_pages_deploy"]["state"], "VALID")
        self.assertEqual(report["evidence"]["candidate_localization_ready"]["state"], "INVALID")
        self.assertEqual(gate["state"], "CLOSED")
        self.assertEqual(gate["proof_state"], "INVALID")
        self.assertEqual(gate["terminal_causes"], ["candidate_localization_ready"])

    def test_postdeploy_health_failure_does_not_need_to_be_the_predeploy_gate(self) -> None:
        report = self.evaluate()
        gate = report["gates"]["candidate_may_enter_deploy"]
        self.assertNotIn("candidate_triggered_health", gate["terminal_causes"])
        self.assertEqual(report["evidence"]["candidate_triggered_health"]["state"], "INVALID")

    def test_fixing_localization_alone_does_not_invent_missing_release_authority(self) -> None:
        repaired = copy.deepcopy(self.receipt)
        evidence(repaired, "candidate_localization_ready")["status"] = "PASS"
        report = self.evaluate(repaired)
        gate = report["gates"]["candidate_may_enter_deploy"]
        self.assertEqual(gate["state"], "CLOSED")
        self.assertEqual(gate["proof_state"], "UNKNOWN")

    def test_complete_positive_predeploy_proof_can_open_without_postdeploy_receipts(self) -> None:
        proven = copy.deepcopy(self.receipt)
        for eid in (
            "candidate_arb_public_safe",
            "candidate_six_release_gates",
            "publication_authority",
            "candidate_localization_ready",
        ):
            evidence(proven, eid)["status"] = "PASS"
        # Footnote: this gate intentionally ends before deployment. A browser/live-health
        # receipt is causally impossible until after deployment, so requiring it here
        # would turn a precondition into a circular postcondition.
        report = self.evaluate(proven)
        self.assertEqual(report["gates"]["candidate_may_enter_deploy"]["state"], "OPEN")
        self.assertEqual(report["gates"]["advance_candidate_current_edition"]["state"], "CLOSED")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NewsletterLocalizationFieldTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
