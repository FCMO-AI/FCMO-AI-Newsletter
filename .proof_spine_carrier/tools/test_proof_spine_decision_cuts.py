#!/usr/bin/env python3
"""Universal regressions for Proof Spine coherent decision cuts / decision leases."""
from __future__ import annotations
import copy
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
assert SPEC.loader
SPEC.loader.exec_module(m)
NOW = datetime(2026, 9, 18, 5, 1, tzinfo=timezone.utc)


def receipt(status="PASS"):
    return {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_PROJECT_RECEIPT",
        "authority": "EVIDENCE_ONLY",
        "project": {"id": "fixture", "repository": "FCMO-AI/fixture"},
        "observed_at": "2026-09-18T05:00:00Z",
        "scope": {"surface": "mutable_action"},
        "evidence": [
            {"id": "structure_valid", "status": "PASS", "causal_root": "fixture:structure", "observed_at": "2026-09-18T05:00:00Z"},
            {"id": "invalidation_clear", "status": status, "causal_root": "fixture:invalidator", "observed_at": "2026-09-18T05:00:00Z"},
        ],
        "local_decisions": [],
    }


def spec():
    return {
        "schema_version": 2,
        "mission": {
            "objective": "Admit a mutable action only from a complete current decision cut.",
            "context": {"project_id": "fixture", "repository": "FCMO-AI/fixture", "surface": "mutable_action"},
        },
        "freshness_requirements": {
            "structure_valid": {"max_age_hours": 1},
            "invalidation_clear": {"max_age_hours": 1},
        },
        "decision_cuts": [
            {
                "id": "fixture_action_lease",
                "gate_id": "admit_action",
                "required_evidence": ["structure_valid", "invalidation_clear"],
                "mutable": True,
            }
        ],
        "claims": [
            {"id": "action_lease_current", "rule": {"all": ["structure_valid", "invalidation_clear"]}}
        ],
        "gates": [
            {
                "id": "admit_action",
                "action": "Represent mutable action as currently admitted",
                "behavior": "block_unless_valid",
                "rule": {"all": ["action_lease_current"]},
            }
        ],
    }


class DecisionCutTests(unittest.TestCase):
    def test_complete_current_cut_opens(self):
        result = m.evaluate_project(spec(), receipt(), NOW, ROOT)
        self.assertEqual(result["proof_report"]["gates"]["admit_action"]["state"], "OPEN")
        self.assertEqual(result["decision_cuts"][0]["required_evidence"], ["structure_valid", "invalidation_clear"])

    def test_active_invalidator_closes_without_poisoning_structure(self):
        result = m.evaluate_project(spec(), receipt("FAIL"), NOW, ROOT)
        self.assertEqual(result["proof_report"]["evidence"]["structure_valid"]["state"], "VALID")
        self.assertEqual(result["proof_report"]["evidence"]["invalidation_clear"]["state"], "INVALID")
        self.assertEqual(result["proof_report"]["gates"]["admit_action"]["state"], "CLOSED")

    def test_required_surface_must_actually_feed_gate(self):
        s = spec()
        s["claims"][0]["rule"] = {"all": ["structure_valid"]}
        with self.assertRaises(m.engine.ProofError):
            m.evaluate_project(s, receipt(), NOW, ROOT)

    def test_missing_required_runtime_surface_fails_contract_closed(self):
        r = receipt()
        r["evidence"] = [r["evidence"][0]]
        with self.assertRaises(m.engine.ProofError):
            m.evaluate_project(spec(), r, NOW, ROOT)

    def test_mutable_cut_requires_reviewed_freshness_for_each_nonstable_surface(self):
        s = spec()
        del s["freshness_requirements"]["invalidation_clear"]
        with self.assertRaises(m.engine.ProofError):
            m.evaluate_project(s, receipt(), NOW, ROOT)

    def test_explicit_stable_surface_can_omit_ttl(self):
        s = spec()
        del s["freshness_requirements"]["invalidation_clear"]
        s["decision_cuts"][0]["stable_evidence"] = ["invalidation_clear"]
        result = m.evaluate_project(s, receipt(), NOW, ROOT)
        self.assertEqual(result["proof_report"]["gates"]["admit_action"]["state"], "OPEN")

    def test_gate_dependency_cannot_hide_outside_reviewed_cut(self):
        s = spec()
        r = receipt()
        r["evidence"].append(
            {"id": "hidden_mutable", "status": "PASS", "causal_root": "fixture:hidden", "observed_at": "2026-09-18T05:00:00Z"}
        )
        s["claims"][0]["rule"] = {"all": ["structure_valid", "invalidation_clear", "hidden_mutable"]}
        # Footnote: before the completeness hardening this extra primitive could feed
        # the gate while remaining absent from required_evidence, so it escaped the
        # reviewed decision-lease freshness surface. The contract must reject that gap.
        with self.assertRaises(m.engine.ProofError):
            m.evaluate_project(s, r, NOW, ROOT)

    def test_reviewed_cut_can_cover_additional_gate_dependency(self):
        s = spec()
        r = receipt()
        r["evidence"].append(
            {"id": "extra_current_state", "status": "PASS", "causal_root": "fixture:extra", "observed_at": "2026-09-18T05:00:00Z"}
        )
        s["claims"][0]["rule"] = {"all": ["structure_valid", "invalidation_clear", "extra_current_state"]}
        s["decision_cuts"][0]["required_evidence"].append("extra_current_state")
        s["freshness_requirements"]["extra_current_state"] = {"max_age_hours": 1}
        # Footnote: expanding the reviewed cut and its freshness contract is the valid
        # path when project law genuinely adds another causal prerequisite.
        result = m.evaluate_project(s, r, NOW, ROOT)
        self.assertEqual(result["proof_report"]["gates"]["admit_action"]["state"], "OPEN")
        self.assertIn("extra_current_state", result["decision_cuts"][0]["transitive_gate_evidence"])

    def test_optional_alternative_can_stay_nonrequired_when_freshness_bound(self):
        s = spec()
        r = receipt()
        r["evidence"].append(
            {"id": "alternate_path", "status": "PASS", "causal_root": "fixture:alternate", "observed_at": "2026-09-18T05:00:00Z"}
        )
        s["claims"][0]["rule"] = {
            "any": [
                {"all": ["structure_valid", "invalidation_clear"]},
                "alternate_path",
            ]
        }
        s["freshness_requirements"]["alternate_path"] = {"max_age_hours": 1}
        # Footnote: an alternative enabling path participates in the reviewed lease
        # through freshness without becoming an always-present required surface.
        # This preserves legitimate any/at_least semantics while closing zombie paths.
        result = m.evaluate_project(s, r, NOW, ROOT)
        self.assertEqual(result["proof_report"]["gates"]["admit_action"]["state"], "OPEN")
        self.assertNotIn("alternate_path", result["decision_cuts"][0]["required_evidence"])
        self.assertIn("alternate_path", result["decision_cuts"][0]["transitive_gate_evidence"])

    def test_project_evaluation_emits_byte_addressed_decision_receipt(self):
        s = spec()
        result = m.evaluate_project(s, receipt(), NOW, ROOT)
        dr = result["decision_receipt"]
        self.assertEqual(dr["kind"], "FCMO_PROOF_SPINE_DECISION_RECEIPT")
        self.assertEqual(dr["proofspec_digest"], m.canonical_sha256(s))
        self.assertEqual(dr["effective_evidence_digest"], "sha256:" + result["effective_evidence_digest"])
        self.assertEqual(dr["gate_decisions"], result["proof_report"]["gates"])
        self.assertEqual(result["decision_receipt_digest"], m.canonical_sha256(dr))

    def test_decision_receipt_binds_contract_and_gate_bytes(self):
        first = m.evaluate_project(spec(), receipt(), NOW, ROOT)
        same = m.evaluate_project(spec(), receipt(), NOW, ROOT)
        self.assertEqual(first["decision_receipt_digest"], same["decision_receipt_digest"])

        changed_spec = spec()
        changed_spec["mission"]["objective"] += " Contract bytes intentionally changed."
        changed = m.evaluate_project(changed_spec, receipt(), NOW, ROOT)
        self.assertNotEqual(first["decision_receipt_digest"], changed["decision_receipt_digest"])

        tampered = copy.deepcopy(first["decision_receipt"])
        tampered["gate_decisions"]["admit_action"]["state"] = "CLOSED"
        # Footnote: calibration may cite the receipt digest, but the digest only means
        # something if any later mutation of the emitted decision changes its identity.
        self.assertNotEqual(first["decision_receipt_digest"], m.canonical_sha256(tampered))

    def test_unrelated_red_evidence_does_not_contaminate_cut(self):
        r = receipt()
        r["evidence"].append(
            {"id": "unrelated", "status": "FAIL", "causal_root": "fixture:unrelated", "observed_at": "2026-09-18T05:00:00Z"}
        )
        result = m.evaluate_project(spec(), r, NOW, ROOT)
        self.assertEqual(result["proof_report"]["gates"]["admit_action"]["state"], "OPEN")


if __name__ == "__main__":
    unittest.main()
