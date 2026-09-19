#!/usr/bin/env python3
"""Focused adversarial tests for universal Proof Spine temporal integrity."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODULE_SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
federation = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = federation
MODULE_SPEC.loader.exec_module(federation)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def receipt(project_id: str, repository: str, observed_at: str, evidence: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_PROJECT_RECEIPT",
        "authority": "EVIDENCE_ONLY",
        "project": {"id": project_id, "repository": repository},
        "observed_at": observed_at,
        "scope": {"subject": "temporal-test"},
        "evidence": evidence,
        "local_decisions": [],
        "claim_boundary": "Synthetic temporal-integrity fixture only.",
    }


def evidence(eid: str, *, status: str = "PASS", observed_at: str | None = None, max_age_hours=None) -> dict:
    item = {"id": eid, "status": status, "causal_root": eid}
    if observed_at is not None:
        item["observed_at"] = observed_at
    if max_age_hours is not None:
        item["max_age_hours"] = max_age_hours
    return item


def project_spec(*, freshness: dict | None = None) -> dict:
    spec = {
        "schema_version": 2,
        "mission": {
            "objective": "Represent one temporally honest premise.",
            "context": {
                "project_id": "alpha",
                "repository": "FCMO-AI/alpha"
            }
        },
        "claims": [{"id": "ready", "rule": {"all": ["e"]}}],
        "gates": [
            {
                "id": "represent_ready",
                "action": "Represent premise as ready",
                "behavior": "block_unless_valid",
                "rule": {"all": ["ready"]},
            }
        ],
    }
    if freshness is not None:
        spec["freshness_requirements"] = freshness
    # Footnote: project mode intentionally binds fixture identity in the reviewed
    # contract. The receipt may report who it is, but must never self-select the
    # project/repository whose gates it is allowed to influence.
    return spec


def federation_spec(max_age_hours: float) -> dict:
    return {
        "schema_version": 2,
        "mission": {"objective": "Represent one federated temporally honest premise.", "context": {}},
        "federation": {
            "receipt_requirements": {
                "alpha": {"repository": "FCMO-AI/alpha"}
            },
            "freshness_requirements": {
                "alpha::e": {"max_age_hours": max_age_hours}
            }
        },
        "claims": [{"id": "ready", "rule": {"all": ["alpha::e"]}}],
        "gates": [
            {
                "id": "represent_ready",
                "action": "Represent federated premise as ready",
                "behavior": "block_unless_valid",
                "rule": {"all": ["ready"]},
            }
        ],
    }


class TemporalIntegrityTests(unittest.TestCase):
    def test_evidence_cannot_be_observed_after_its_receipt(self) -> None:
        candidate = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e", observed_at="2026-09-15T12:00:00Z")],
        )
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_project(project_spec(), candidate, NOW, ROOT)

    def test_future_declared_federation_receipt_is_rejected(self) -> None:
        alpha = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e", observed_at="2026-09-15T11:59:00Z")],
        )
        future_beta = receipt(
            "beta",
            "FCMO-AI/beta",
            "2026-09-15T13:00:00Z",
            [evidence("unused", observed_at="2026-09-15T11:59:00Z")],
        )
        spec = {
            "schema_version": 2,
            "mission": {"objective": "Refuse impossible envelope provenance.", "context": {}},
            "federation": {
                "receipt_requirements": {
                    "alpha": {"repository": "FCMO-AI/alpha"},
                    "beta": {"repository": "FCMO-AI/beta"},
                }
            },
            "claims": [{"id": "ready", "rule": {"all": ["alpha::e"]}}],
            "gates": [
                {
                    "id": "represent_ready",
                    "action": "Represent alpha as ready",
                    "behavior": "block_unless_valid",
                    "rule": {"all": ["ready"]},
                }
            ],
        }
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_federation(spec, [alpha, future_beta], NOW, ROOT)

    def test_contract_ttl_stales_pass_without_producer_ttl(self) -> None:
        candidate = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e", observed_at="2026-09-15T10:00:00Z")],
        )
        result = federation.evaluate_project(
            project_spec(freshness={"e": {"max_age_hours": 1}}),
            candidate,
            NOW,
            ROOT,
        )
        self.assertEqual(result["proof_report"]["evidence"]["e"]["state"], "STALE")
        self.assertEqual(result["freshness_requirements"][0]["effective_max_age_hours"], 1.0)

    def test_missing_time_under_contract_ttl_is_unknown_not_refreshed(self) -> None:
        candidate = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e")],
        )
        result = federation.evaluate_project(
            project_spec(freshness={"e": {"max_age_hours": 1}}),
            candidate,
            NOW,
            ROOT,
        )
        self.assertEqual(result["proof_report"]["evidence"]["e"]["state"], "UNKNOWN")
        self.assertEqual(result["freshness_requirements"][0]["action"], "missing_observed_at")

    def test_producer_can_tighten_but_cannot_widen_contract_ttl(self) -> None:
        too_generous = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e", observed_at="2026-09-15T10:00:00Z", max_age_hours=999)],
        )
        result = federation.evaluate_project(
            project_spec(freshness={"e": {"max_age_hours": 1}}),
            too_generous,
            NOW,
            ROOT,
        )
        self.assertEqual(result["proof_report"]["evidence"]["e"]["state"], "STALE")
        self.assertEqual(result["freshness_requirements"][0]["effective_max_age_hours"], 1.0)

        tighter = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e", observed_at="2026-09-15T11:15:00Z", max_age_hours=0.5)],
        )
        tighter_result = federation.evaluate_project(
            project_spec(freshness={"e": {"max_age_hours": 1}}),
            tighter,
            NOW,
            ROOT,
        )
        self.assertEqual(tighter_result["proof_report"]["evidence"]["e"]["state"], "STALE")
        self.assertEqual(tighter_result["freshness_requirements"][0]["effective_max_age_hours"], 0.5)

    def test_raw_federated_evidence_digest_is_independent_from_freshness_contract(self) -> None:
        alpha = receipt(
            "alpha",
            "FCMO-AI/alpha",
            "2026-09-15T11:59:00Z",
            [evidence("e", observed_at="2026-09-15T10:00:00Z")],
        )
        strict = federation.evaluate_federation(federation_spec(1), [alpha], NOW, ROOT)
        loose = federation.evaluate_federation(federation_spec(3), [alpha], NOW, ROOT)

        # Footnote: changing the reviewed judge must change the proofspec/effective
        # evaluation, but it must not rewrite the identity hash of the supplied evidence.
        self.assertEqual(strict["federated_evidence_digest"], loose["federated_evidence_digest"])
        self.assertNotEqual(strict["effective_evidence_digest"], loose["effective_evidence_digest"])
        self.assertNotEqual(
            strict["proof_report"]["proofspec_digest"],
            loose["proof_report"]["proofspec_digest"],
        )
        self.assertEqual(strict["proof_report"]["gates"]["represent_ready"]["proof_state"], "STALE")
        self.assertEqual(loose["proof_report"]["gates"]["represent_ready"]["proof_state"], "VALID")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TemporalIntegrityTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
