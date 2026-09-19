#!/usr/bin/env python3
"""Regression tests for the FCMO-wide Proof Spine federation boundary."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC_PATH = ROOT / "commons/experiments/2026-09-15_FCMO_PROOF_SPINE_UNIVERSAL_MULTI_PROJECT_PROOFSPEC_v0.3.json"

MODULE_SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
federation = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = federation
MODULE_SPEC.loader.exec_module(federation)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def receipt(project_id: str, repository: str, evidence: list[dict], *, scope: dict | None = None) -> dict:
    return {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_PROJECT_RECEIPT",
        "authority": "EVIDENCE_ONLY",
        "project": {"id": project_id, "repository": repository},
        "observed_at": "2026-09-15T11:55:00Z",
        "scope": scope if scope is not None else {"subject": "test-fixture"},
        "evidence": evidence,
        "local_decisions": [],
        "claim_boundary": "Synthetic regression fixture only; not current project state."
    }


def ev(eid: str, status: str = "PASS", root: str | None = None, **extra) -> dict:
    item = {
        "id": eid,
        "status": status,
        "causal_root": root or eid,
        "observed_at": "2026-09-15T11:55:00Z",
    }
    item.update(extra)
    return item


def member_requirements(*pairs: tuple[str, str]) -> dict:
    return {pid: {"repository": repository} for pid, repository in pairs}


class ProofSpineFederationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        self.newsletter = receipt(
            "newsletter",
            "FCMO-AI/FCMO-AI-Newsletter",
            [ev("public_material_sync")],
        )
        self.cmpct = receipt(
            "cmpct",
            "FCMO-AI/.CMPCT",
            [
                ev("benchmark_semantics"),
                ev("archive_size_parity"),
                ev("timing_parity"),
                ev("portability"),
            ],
        )
        self.blm = receipt(
            "blm",
            "Magyarmex/BLM",
            [
                ev("scientific_integrity"),
                ev("matched_control"),
                ev("scale_regime"),
                ev("q4_behavior"),
            ],
        )

    def evaluate(self, *receipts: dict) -> dict:
        return federation.evaluate_federation(self.spec, list(receipts), NOW, ROOT)["proof_report"]

    def test_same_engine_handles_three_materially_different_fcmo_domains(self) -> None:
        report = self.evaluate(self.newsletter, self.cmpct, self.blm)
        self.assertEqual(
            sorted(report["summary"]["open_gates"]),
            [
                "represent_blm_scientific_promotion_proven",
                "represent_cmpct_release_parity_proven",
                "represent_newsletter_materially_synced",
            ],
        )
        self.assertEqual(report["summary"]["closed_gates"], [])

    def test_cmpct_release_regression_does_not_poison_blm_or_newsletter(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")["status"] = "FAIL"
        report = self.evaluate(self.newsletter, cmpct, self.blm)
        self.assertEqual(report["gates"]["represent_cmpct_release_parity_proven"]["state"], "CLOSED")
        self.assertEqual(report["gates"]["represent_cmpct_release_parity_proven"]["proof_state"], "INVALID")
        self.assertEqual(report["gates"]["represent_blm_scientific_promotion_proven"]["state"], "OPEN")
        self.assertEqual(report["gates"]["represent_newsletter_materially_synced"]["state"], "OPEN")

    def test_blm_unknown_scale_regime_does_not_poison_other_projects(self) -> None:
        blm = json.loads(json.dumps(self.blm))
        next(item for item in blm["evidence"] if item["id"] == "scale_regime")["status"] = "UNKNOWN"
        report = self.evaluate(self.newsletter, self.cmpct, blm)
        self.assertEqual(report["gates"]["represent_blm_scientific_promotion_proven"]["state"], "CLOSED")
        self.assertEqual(report["gates"]["represent_blm_scientific_promotion_proven"]["proof_state"], "UNKNOWN")
        self.assertEqual(report["gates"]["represent_cmpct_release_parity_proven"]["state"], "OPEN")
        self.assertEqual(report["gates"]["represent_newsletter_materially_synced"]["state"], "OPEN")

    def test_identical_local_evidence_ids_are_namespaced_not_collided(self) -> None:
        a = receipt("alpha", "FCMO-AI/alpha", [ev("health")])
        b = receipt("beta", "FCMO-AI/beta", [ev("health")])
        envelope, _ = federation.federated_envelope([a, b])
        self.assertEqual([item["id"] for item in envelope["evidence"]], ["alpha::health", "beta::health"])

    def test_local_causal_roots_are_isolated_by_default(self) -> None:
        a = receipt("alpha", "FCMO-AI/alpha", [ev("e", root="same-short-name")])
        b = receipt("beta", "FCMO-AI/beta", [ev("e", root="same-short-name")])
        envelope, _ = federation.federated_envelope([a, b])
        roots = {item["causal_root"] for item in envelope["evidence"]}
        self.assertEqual(roots, {"alpha::same-short-name", "beta::same-short-name"})

    def test_reviewed_causal_equivalence_prevents_fake_independence(self) -> None:
        a = receipt("alpha", "FCMO-AI/alpha", [ev("e")])
        b = receipt("beta", "FCMO-AI/beta", [ev("e")])
        spec = {
            "schema_version": 2,
            "mission": {"objective": "Require two causally independent project observations.", "context": {}},
            "federation": {
                "receipt_requirements": member_requirements(
                    ("alpha", "FCMO-AI/alpha"),
                    ("beta", "FCMO-AI/beta"),
                ),
                "causal_equivalence": [
                    {
                        "id": "one-real-upstream",
                        "members": ["alpha::e", "beta::e"]
                    }
                ]
            },
            "claims": [
                {
                    "id": "two_independent",
                    "rule": {
                        "at_least": {
                            "count": 2,
                            "of": ["alpha::e", "beta::e"],
                            "independent": True,
                        }
                    },
                }
            ],
            "gates": [
                {
                    "id": "independence_gate",
                    "action": "Treat corroboration as independent",
                    "behavior": "block_unless_valid",
                    "rule": {"all": ["two_independent"]},
                }
            ],
        }
        result = federation.evaluate_federation(spec, [a, b], NOW, ROOT)
        report = result["proof_report"]
        self.assertEqual(report["gates"]["independence_gate"]["state"], "CLOSED")
        self.assertEqual(report["gates"]["independence_gate"]["proof_state"], "INVALID")
        self.assertEqual(
            result["federation"]["causal_equivalence"],
            [
                {
                    "id": "one-real-upstream",
                    "members": ["alpha::e", "beta::e"],
                    "causal_root": "federation-cause::one-real-upstream",
                }
            ],
        )

    def test_runtime_producer_cannot_self_declare_shared_causal_root(self) -> None:
        poisoned = receipt(
            "alpha",
            "FCMO-AI/alpha",
            [ev("e", shared_causal_root="shared:self-awarded")],
        )
        with self.assertRaises(federation.engine.ProofError):
            federation.validate_project_receipt(poisoned)

    def test_receipt_cannot_self_author_its_claims_or_gates(self) -> None:
        poisoned = json.loads(json.dumps(self.cmpct))
        poisoned["gates"] = [{"id": "approve_me"}]
        with self.assertRaises(federation.engine.ProofError):
            federation.validate_project_receipt(poisoned)

    def test_receipt_scope_mismatch_is_rejected_before_federation(self) -> None:
        scoped = receipt(
            "cmpct",
            "FCMO-AI/.CMPCT",
            [ev("archive_size_parity", applies_to={"subject": "release-v0.30"})],
            scope={"subject": "release-v0.31"},
        )
        with self.assertRaises(federation.engine.ProofError):
            federation.validate_project_receipt(scoped)

    def test_scope_cannot_override_project_identity(self) -> None:
        poisoned = receipt(
            "cmpct",
            "FCMO-AI/.CMPCT",
            [ev("archive_size_parity")],
            scope={"project_id": "not-cmpct", "subject": "release-v0.30"},
        )
        with self.assertRaises(federation.engine.ProofError):
            federation.validate_project_receipt(poisoned)

    def test_local_evidence_id_cannot_claim_federation_namespace(self) -> None:
        poisoned = receipt("alpha", "FCMO-AI/alpha", [ev("beta::health")])
        with self.assertRaises(federation.engine.ProofError):
            federation.validate_project_receipt(poisoned)

    def test_same_repository_cannot_masquerade_as_two_independent_projects(self) -> None:
        a = receipt("alpha", "FCMO-AI/shared", [ev("e1")])
        b = receipt("beta", "FCMO-AI/shared", [ev("e2")])
        with self.assertRaises(federation.engine.ProofError):
            federation.federated_envelope([a, b])

    def test_repository_case_alias_cannot_fake_two_independent_projects(self) -> None:
        a = receipt("alpha", "FCMO-AI/Shared", [ev("e1")])
        b = receipt("beta", "fcmo-ai/shared", [ev("e2")])
        with self.assertRaises(federation.engine.ProofError):
            federation.federated_envelope([a, b])

    def test_federation_rejects_unreviewed_extra_project(self) -> None:
        extra = receipt("extra", "FCMO-AI/extra", [ev("irrelevant")])
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_federation(
                self.spec,
                [self.newsletter, self.cmpct, self.blm, extra],
                NOW,
                ROOT,
            )

    def test_federation_requires_repository_binding_for_every_member(self) -> None:
        alpha = receipt("alpha", "FCMO-AI/alpha", [ev("e")])
        spec = {
            "schema_version": 2,
            "mission": {"objective": "Bind federation identity.", "context": {}},
            "federation": {"receipt_requirements": {"alpha": {}}},
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
            federation.evaluate_federation(spec, [alpha], NOW, ROOT)

    def test_reviewed_federation_requirement_rejects_wrong_release_scope(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        cmpct["scope"]["subject"] = "release-v0.31"
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_federation(self.spec, [self.newsletter, cmpct, self.blm], NOW, ROOT)

    def test_reviewed_federation_requirement_rejects_wrong_repository(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        cmpct["project"]["repository"] = "FCMO-AI/not-cmpct"
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_federation(self.spec, [self.newsletter, cmpct, self.blm], NOW, ROOT)

    def test_project_mode_requires_reviewed_project_identity(self) -> None:
        unbound_spec = {
            "schema_version": 2,
            "mission": {"objective": "Do not accept self-declared project identity.", "context": {}},
            "claims": [{"id": "ready", "rule": {"all": ["e"]}}],
            "gates": [
                {
                    "id": "represent_ready",
                    "action": "Represent project as ready",
                    "behavior": "block_unless_valid",
                    "rule": {"all": ["ready"]},
                }
            ],
        }
        project_receipt = receipt("alpha", "FCMO-AI/alpha", [ev("e")])
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_project(unbound_spec, project_receipt, NOW, ROOT)

    def test_local_project_contract_context_binds_receipt_scope(self) -> None:
        local_spec = {
            "schema_version": 2,
            "mission": {
                "objective": "Represent one scoped project claim.",
                "context": {
                    "project_id": "cmpct",
                    "repository": "FCMO-AI/.CMPCT",
                    "subject": "release-v0.30"
                }
            },
            "claims": [{"id": "ready", "rule": {"all": ["e"]}}],
            "gates": [
                {
                    "id": "represent_ready",
                    "action": "Represent scoped evidence as ready",
                    "behavior": "block_unless_valid",
                    "rule": {"all": ["ready"]},
                }
            ],
        }
        wrong_scope = receipt(
            "cmpct",
            "FCMO-AI/.CMPCT",
            [ev("e", applies_to={"subject": "release-v0.31"})],
            scope={"subject": "release-v0.31"},
        )
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_project(local_spec, wrong_scope, NOW, ROOT)

    def test_contract_freshness_stales_pass_when_producer_omits_ttl(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        target = next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")
        target["observed_at"] = "2026-09-15T04:00:00Z"
        report = self.evaluate(self.newsletter, cmpct, self.blm)
        self.assertEqual(report["evidence"]["cmpct::archive_size_parity"]["state"], "STALE")
        self.assertEqual(report["gates"]["represent_cmpct_release_parity_proven"]["state"], "CLOSED")

    def test_producer_cannot_widen_reviewed_freshness_window(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        target = next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")
        target["observed_at"] = "2026-09-15T04:00:00Z"
        target["max_age_hours"] = 999
        result = federation.evaluate_federation(self.spec, [self.newsletter, cmpct, self.blm], NOW, ROOT)
        report = result["proof_report"]
        self.assertEqual(report["evidence"]["cmpct::archive_size_parity"]["state"], "STALE")
        applied = {
            row["evidence_id"]: row
            for row in result["federation"]["freshness_requirements"]
        }
        self.assertEqual(applied["cmpct::archive_size_parity"]["effective_max_age_hours"], 6.0)

    def test_producer_may_tighten_but_not_relax_reviewed_freshness(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        target = next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")
        target["observed_at"] = "2026-09-15T11:00:00Z"
        target["max_age_hours"] = 0.5
        result = federation.evaluate_federation(self.spec, [self.newsletter, cmpct, self.blm], NOW, ROOT)
        report = result["proof_report"]
        self.assertEqual(report["evidence"]["cmpct::archive_size_parity"]["state"], "STALE")
        applied = {
            row["evidence_id"]: row
            for row in result["federation"]["freshness_requirements"]
        }
        self.assertEqual(applied["cmpct::archive_size_parity"]["effective_max_age_hours"], 0.5)

    def test_fresh_receipt_cannot_refresh_old_underlying_observation(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        cmpct["observed_at"] = "2026-09-15T11:59:00Z"
        target = next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")
        target["observed_at"] = "2026-09-15T04:00:00Z"
        report = self.evaluate(self.newsletter, cmpct, self.blm)
        self.assertEqual(report["evidence"]["cmpct::archive_size_parity"]["state"], "STALE")

    def test_missing_observation_time_under_reviewed_freshness_becomes_unknown(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        target = next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")
        target.pop("observed_at")
        report = self.evaluate(self.newsletter, cmpct, self.blm)
        self.assertEqual(report["evidence"]["cmpct::archive_size_parity"]["state"], "UNKNOWN")
        self.assertEqual(report["gates"]["represent_cmpct_release_parity_proven"]["proof_state"], "UNKNOWN")

    def test_evidence_observation_after_receipt_is_rejected_as_impossible_provenance(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        target = next(item for item in cmpct["evidence"] if item["id"] == "archive_size_parity")
        target["observed_at"] = "2026-09-15T11:56:00Z"
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_federation(self.spec, [self.newsletter, cmpct, self.blm], NOW, ROOT)

    def test_reviewed_receipt_ttl_stales_entire_old_project_envelope(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        cmpct["observed_at"] = "2026-09-15T01:00:00Z"
        for item in cmpct["evidence"]:
            item["observed_at"] = "2026-09-15T01:00:00Z"
        report = self.evaluate(self.newsletter, cmpct, self.blm)
        self.assertEqual(report["gates"]["represent_cmpct_release_parity_proven"]["proof_state"], "STALE")
        self.assertEqual(report["gates"]["represent_blm_scientific_promotion_proven"]["state"], "OPEN")
        self.assertEqual(report["gates"]["represent_newsletter_materially_synced"]["state"], "OPEN")

    def test_future_project_receipt_timestamp_is_rejected(self) -> None:
        cmpct = json.loads(json.dumps(self.cmpct))
        cmpct["observed_at"] = "2026-09-15T13:00:00Z"
        with self.assertRaises(federation.engine.ProofError):
            federation.evaluate_federation(self.spec, [self.newsletter, cmpct, self.blm], NOW, ROOT)

    def test_local_project_mode_can_make_freshness_contract_owned(self) -> None:
        local_spec = {
            "schema_version": 2,
            "mission": {
                "objective": "Represent fresh project evidence.",
                "context": {
                    "project_id": "alpha",
                    "repository": "FCMO-AI/alpha"
                }
            },
            "freshness_requirements": {"e": {"max_age_hours": 1}},
            "claims": [{"id": "ready", "rule": {"all": ["e"]}}],
            "gates": [
                {
                    "id": "represent_ready",
                    "action": "Represent fresh evidence as ready",
                    "behavior": "block_unless_valid",
                    "rule": {"all": ["ready"]},
                }
            ],
        }
        project_receipt = receipt(
            "alpha",
            "FCMO-AI/alpha",
            [ev("e", observed_at="2026-09-15T10:00:00Z")],
        )
        result = federation.evaluate_project(local_spec, project_receipt, NOW, ROOT)
        self.assertEqual(result["proof_report"]["gates"]["represent_ready"]["proof_state"], "STALE")
        self.assertEqual(result["freshness_requirements"][0]["effective_max_age_hours"], 1.0)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProofSpineFederationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
