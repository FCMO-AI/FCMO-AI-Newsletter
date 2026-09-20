#!/usr/bin/env python3
"""Regression tests for calibration v7 exact adjudication provenance."""
from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

V7_SPEC = importlib.util.spec_from_file_location(
    "calibration_v7", HERE / "proof_spine_calibration_ledger_v7.py"
)
m = importlib.util.module_from_spec(V7_SPEC)
sys.modules[V7_SPEC.name] = m
assert V7_SPEC.loader is not None
V7_SPEC.loader.exec_module(m)

FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "calibration_v6_fixture", HERE / "test_proof_spine_calibration_ledger_v6.py"
)
fx = importlib.util.module_from_spec(FIXTURE_SPEC)
sys.modules[FIXTURE_SPEC.name] = fx
assert FIXTURE_SPEC.loader is not None
FIXTURE_SPEC.loader.exec_module(fx)

ADJUDICATOR_DIGEST = "sha256:" + "7" * 64
ADJUDICATOR_ID = "external-project-local-oracle-v1"
ADJUDICATOR_ROOT = "external-oracle:newsletter-public-origin-v1"
ADJUDICATOR_ESTABLISHED = "2026-09-18T05:40:00Z"


def adjudication_contract() -> dict:
    return {
        "gate": {
            "project_id": "newsletter",
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "gate_id": "candidate_may_enter_deploy",
        },
        "mode": m.ADJUDICATION_CONTRACT_MODE,
        "receipt_kind": m.ADJUDICATION_RECEIPT_KIND,
        "source_authority": m.ADJUDICATION_SOURCE_AUTHORITY,
        "relation_to_spine": m.ADJUDICATION_RELATION,
        "required_subject_keys": ["source_sha", "gate_scope"],
        "mechanism": {
            "id": ADJUDICATOR_ID,
            "origin": "EXTERNAL_INDEPENDENT",
            "contract_digest": ADJUDICATOR_DIGEST,
            "measurement_roots": [ADJUDICATOR_ROOT],
            "evidence_ref_prefixes": ["oracle-run:"],
        },
    }


def plan() -> dict:
    p = fx.plan()
    p["adjudication_contracts"] = [adjudication_contract()]
    return p


def exact_case(p: dict, *, actual: str = "SHOULD_ALLOW") -> tuple[dict, dict]:
    c = fx.case(actual=actual)
    c["enrollment"]["plan_digest"] = m.v6.v5.canonical_digest(p)
    c["adjudication"]["state"] = actual
    c["adjudication"]["basis"] = "Independent project-local oracle verdict"
    c["adjudication"]["mechanism"] = {
        "id": ADJUDICATOR_ID,
        "origin": "EXTERNAL_INDEPENDENT",
        "contract_digest": ADJUDICATOR_DIGEST,
        "established_at": ADJUDICATOR_ESTABLISHED,
        "evidence_refs": ["oracle-run:fixture-001"],
        "measurement_roots": [ADJUDICATOR_ROOT],
    }
    receipt = {
        "schema_version": 1,
        "kind": m.ADJUDICATION_RECEIPT_KIND,
        "authority": m.ADJUDICATION_RECEIPT_AUTHORITY,
        "source_authority": m.ADJUDICATION_SOURCE_AUTHORITY,
        "relation_to_spine": m.ADJUDICATION_RELATION,
        "project": copy.deepcopy(c["project"]),
        "gate_id": c["gate"]["id"],
        "subject": copy.deepcopy(c["subject"]),
        "state": c["adjudication"]["state"],
        "observed_at": c["adjudication"]["observed_at"],
        "basis": c["adjudication"]["basis"],
        "mechanism": copy.deepcopy(c["adjudication"]["mechanism"]),
    }
    digest = m.v6.v5.canonical_digest(receipt)
    c["adjudication"]["provenance"] = {
        "state": "EXECUTED",
        "receipt_kind": m.ADJUDICATION_RECEIPT_KIND,
        "receipt_digest": digest,
    }
    return c, receipt


class CalibrationV7Tests(unittest.TestCase):
    def setup_bundle(self, p: dict | None = None):
        p = p or plan()
        temp, root, sha, committed_at = fx.git_repo_with_plan(p)
        self.addCleanup(temp.cleanup)
        return p, root, fx.registration(p, sha, committed_at)

    def test_exact_preregistered_adjudication_receipt_scores(self):
        p, root, reg = self.setup_bundle()
        c, adjudication = exact_case(p)
        report = m.calibrate(
            [p],
            [reg],
            [fx.coverage()],
            [fx.decision_receipt()],
            [adjudication],
            [c],
            git_root=root,
        )
        event = report["events"][0]
        self.assertEqual(report["schema_version"], 7)
        self.assertEqual(event["classification"], "TRUE_ALLOW")
        self.assertTrue(event["adjudication_receipt_verified"])
        self.assertEqual(report["specificity"]["rate"], 1.0)
        self.assertEqual(report["exact_adjudication_receipt_event_count"], 1)

    def test_missing_exact_adjudication_bytes_withholds_source_frame(self):
        p, root, reg = self.setup_bundle()
        c, _ = exact_case(p)
        report = m.calibrate(
            [p],
            [reg],
            [fx.coverage()],
            [fx.decision_receipt()],
            [],
            [c],
            git_root=root,
        )
        event = report["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn(
            "ADJUDICATION_RECEIPT_BYTES_UNAVAILABLE",
            event["scoreability_reasons"],
        )
        self.assertIsNone(report["specificity"]["rate"])
        self.assertEqual(
            report["specificity"]["withheld_reason"],
            "INCOMPLETE_SCOREABLE_SOURCE_DENOMINATOR",
        )

    def test_post_outcome_adjudicator_switch_cannot_score(self):
        p, root, reg = self.setup_bundle()
        c, receipt = exact_case(p)
        switched = copy.deepcopy(receipt)
        switched["mechanism"]["id"] = "outcome-selected-oracle"
        switched["mechanism"]["contract_digest"] = "sha256:" + "8" * 64
        switched_digest = m.v6.v5.canonical_digest(switched)
        c["adjudication"]["mechanism"] = copy.deepcopy(switched["mechanism"])
        c["adjudication"]["provenance"]["receipt_digest"] = switched_digest

        report = m.calibrate(
            [p],
            [reg],
            [fx.coverage()],
            [fx.decision_receipt()],
            [switched],
            [c],
            git_root=root,
        )
        event = report["events"][0]
        self.assertEqual(event["classification"], "UNSCORABLE")
        self.assertIn(
            "ADJUDICATION_OUTSIDE_PREREGISTERED_CONTRACT",
            event["scoreability_reasons"],
        )
        self.assertIsNone(report["specificity"]["rate"])

    def test_case_cannot_relabel_exact_adjudication_receipt(self):
        p, root, reg = self.setup_bundle()
        c, receipt = exact_case(p)
        c["adjudication"]["state"] = "SHOULD_BLOCK"
        with self.assertRaises(m.v6.v5.v4.CalibrationError):
            m.calibrate(
                [p],
                [reg],
                [fx.coverage()],
                [fx.decision_receipt()],
                [receipt],
                [c],
                git_root=root,
            )

    def test_plan_requires_one_adjudication_contract_per_registered_gate(self):
        p = fx.plan()
        p["adjudication_contracts"] = []
        with self.assertRaises(m.v6.v5.v4.CalibrationError):
            m.index_adjudication_contracts({fx.PLAN_ID: p})

    def test_required_subject_keys_are_preregistered(self):
        p = plan()
        p["adjudication_contracts"][0]["required_subject_keys"].append(
            "source_event_id"
        )
        p, root, reg = self.setup_bundle(p)
        c, receipt = exact_case(p)
        report = m.calibrate(
            [p],
            [reg],
            [fx.coverage()],
            [fx.decision_receipt()],
            [receipt],
            [c],
            git_root=root,
        )
        event = report["events"][0]
        self.assertIn(
            "ADJUDICATION_SUBJECT_OUTSIDE_PREREGISTERED_CONTRACT",
            event["scoreability_reasons"],
        )
        self.assertIsNone(report["specificity"]["rate"])

    def test_hand_reconstructed_adjudication_without_receipt_provenance_cannot_score(self):
        p, root, reg = self.setup_bundle()
        c, receipt = exact_case(p)
        del c["adjudication"]["provenance"]
        report = m.calibrate(
            [p],
            [reg],
            [fx.coverage()],
            [fx.decision_receipt()],
            [receipt],
            [c],
            git_root=root,
        )
        self.assertIn(
            "ADJUDICATION_RECEIPT_PROVENANCE_MISSING",
            report["events"][0]["scoreability_reasons"],
        )
        self.assertIsNone(report["specificity"]["rate"])

    def test_exact_receipt_evidence_namespace_is_preregistered(self):
        p, root, reg = self.setup_bundle()
        c, receipt = exact_case(p)
        receipt["mechanism"]["evidence_refs"] = ["handpicked:fixture-001"]
        c["adjudication"]["mechanism"]["evidence_refs"] = ["handpicked:fixture-001"]
        digest = m.v6.v5.canonical_digest(receipt)
        c["adjudication"]["provenance"]["receipt_digest"] = digest
        report = m.calibrate(
            [p],
            [reg],
            [fx.coverage()],
            [fx.decision_receipt()],
            [receipt],
            [c],
            git_root=root,
        )
        self.assertIn(
            "ADJUDICATION_OUTSIDE_PREREGISTERED_EVIDENCE_NAMESPACE",
            report["events"][0]["scoreability_reasons"],
        )
        self.assertIsNone(report["specificity"]["rate"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
