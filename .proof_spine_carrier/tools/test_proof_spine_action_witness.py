#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from proof_spine_action_witness import WitnessError, evaluate_action_witness


BASE_CONTRACT = {
    "schema_version": 1,
    "kind": "FCMO_PROOF_SPINE_ACTION_WITNESS_CONTRACT",
    "gate_id": "candidate_may_enter_deploy",
    "action_kind": "deployment",
    "direct_subject_keys": ["project_id", "repository", "source_head_sha"],
    "continuity_subject_keys": ["material_defect_ids"],
    "time_boundary_preference": ["queued_at", "created_at", "started_at"],
}
BASE_PROOF = {
    "schema_version": 1,
    "kind": "FCMO_PROOF_SPINE_GATE_OBSERVATION",
    "gate_id": "candidate_may_enter_deploy",
    "gate_state": "CLOSED",
    "proof_state": "INVALID",
    "evaluated_at": "2026-09-16T19:22:02.358706Z",
    "subject": {
        "project_id": "newsletter",
        "repository": "FCMO-AI/FCMO-AI-Newsletter",
        "source_head_sha": "1af947d",
        "material_defect_ids": ["FCMO-7EBD0FA07C12"],
    },
}
BASE_ACTION = {
    "schema_version": 1,
    "kind": "FCMO_PROOF_SPINE_OBSERVED_ACTION",
    "action_kind": "deployment",
    "action_id": "github-actions:35151946023",
    "outcome": "success",
    "time_boundaries": {
        "created_at": "2026-09-16T21:21:42Z",
        "started_at": "2026-09-16T21:21:42Z",
    },
    "subject": {
        "project_id": "newsletter",
        "repository": "FCMO-AI/FCMO-AI-Newsletter",
        "source_head_sha": "1af947d",
    },
}
BASE_CORROBORATION = {
    "schema_version": 1,
    "kind": "FCMO_PROOF_SPINE_SUBJECT_CORROBORATION",
    "observed_at": "2026-09-16T21:23:20.2897118Z",
    "subject": {
        "project_id": "newsletter",
        "repository": "FCMO-AI/FCMO-AI-Newsletter",
        "source_head_sha": "1af947d",
        "material_defect_ids": ["FCMO-7EBD0FA07C12"],
    },
}

BASE_DECISION_RECEIPT = {
    "schema_version": 1,
    "kind": "FCMO_PROOF_SPINE_DECISION_RECEIPT",
    "authority": "EVIDENCE_ONLY",
    "mode": "FCMO_PROOF_SPINE_PROJECT",
    "evaluated_at": "2026-09-16T19:22:02.358706Z",
    "context": {
        "project_id": "newsletter",
        "repository": "FCMO-AI/FCMO-AI-Newsletter",
        "source_head_sha": "1af947d",
        "material_defect_ids": ["FCMO-7EBD0FA07C12"],
    },
    "proofspec_digest": "sha256:" + "a" * 64,
    "source_evidence_digest": "sha256:" + "b" * 64,
    "effective_evidence_digest": "sha256:" + "c" * 64,
    "proof_report_digest": "sha256:" + "d" * 64,
    "gate_decisions": {
        "candidate_may_enter_deploy": {
            "state": "CLOSED",
            "proof_state": "INVALID",
            "reasons": ["candidate_localization_ready"],
        }
    },
}


class ActionWitnessTests(unittest.TestCase):
    def test_exact_decision_receipt_binds_executed_gate_bytes(self) -> None:
        contract = copy.deepcopy(BASE_CONTRACT)
        contract["require_exact_decision_receipt"] = True
        result = evaluate_action_witness(
            contract,
            BASE_DECISION_RECEIPT,
            BASE_ACTION,
            BASE_CORROBORATION,
        )
        self.assertEqual(result["classification"], "PRE_ACTION_CLOSED_CORROBORATED")
        self.assertEqual(result["proof_binding"]["mode"], "EXACT_DECISION_RECEIPT")
        self.assertTrue(result["proof_binding"]["exact_executed"])
        self.assertEqual(
            result["proof_binding"]["decision_receipt_digest"],
            result["digests"]["decision_receipt"],
        )
        self.assertIsNone(result["digests"]["proof_observation"])

    def test_exact_contract_rejects_parallel_legacy_summary(self) -> None:
        contract = copy.deepcopy(BASE_CONTRACT)
        contract["require_exact_decision_receipt"] = True
        # Footnote: a hand-authored gate summary may describe the same facts, but it
        # cannot impersonate the executed decision bytes when the reviewed contract
        # explicitly requires exact binding.
        with self.assertRaises(WitnessError):
            evaluate_action_witness(contract, BASE_PROOF, BASE_ACTION, BASE_CORROBORATION)

    def test_decision_receipt_must_contain_reviewed_gate(self) -> None:
        contract = copy.deepcopy(BASE_CONTRACT)
        contract["require_exact_decision_receipt"] = True
        receipt = copy.deepcopy(BASE_DECISION_RECEIPT)
        del receipt["gate_decisions"]["candidate_may_enter_deploy"]
        with self.assertRaises(WitnessError):
            evaluate_action_witness(contract, receipt, BASE_ACTION, BASE_CORROBORATION)

    def test_closed_gate_before_action_with_continuity_is_corroborated(self) -> None:
        result = evaluate_action_witness(BASE_CONTRACT, BASE_PROOF, BASE_ACTION, BASE_CORROBORATION)
        self.assertEqual(result["classification"], "PRE_ACTION_CLOSED_CORROBORATED")
        self.assertTrue(result["temporal_relation"]["proof_precedes_action"])
        self.assertAlmostEqual(result["temporal_relation"]["lead_seconds"], 7179.641294, places=6)
        self.assertEqual(result["subject_binding"]["continuity"]["state"], "MATCH")

    def test_same_sha_without_required_continuity_is_underbound(self) -> None:
        result = evaluate_action_witness(BASE_CONTRACT, BASE_PROOF, BASE_ACTION)
        self.assertEqual(result["classification"], "SUBJECT_UNDERBOUND")

    def test_direct_identity_mismatch_wins_over_chronology(self) -> None:
        action = copy.deepcopy(BASE_ACTION)
        action["subject"]["source_head_sha"] = "different"
        result = evaluate_action_witness(BASE_CONTRACT, BASE_PROOF, action, BASE_CORROBORATION)
        self.assertEqual(result["classification"], "SUBJECT_MISMATCH")

    def test_changed_material_identity_is_subject_mismatch(self) -> None:
        corroboration = copy.deepcopy(BASE_CORROBORATION)
        corroboration["subject"]["material_defect_ids"] = ["OTHER"]
        result = evaluate_action_witness(BASE_CONTRACT, BASE_PROOF, BASE_ACTION, corroboration)
        self.assertEqual(result["classification"], "SUBJECT_MISMATCH")

    def test_proof_after_action_is_post_action_only(self) -> None:
        proof = copy.deepcopy(BASE_PROOF)
        proof["evaluated_at"] = "2026-09-16T22:00:00Z"
        corroboration = copy.deepcopy(BASE_CORROBORATION)
        corroboration["observed_at"] = "2026-09-16T22:10:00Z"
        result = evaluate_action_witness(BASE_CONTRACT, proof, BASE_ACTION, corroboration)
        self.assertEqual(result["classification"], "POST_ACTION_ONLY")

    def test_corroboration_before_action_is_temporally_invalid(self) -> None:
        corroboration = copy.deepcopy(BASE_CORROBORATION)
        corroboration["observed_at"] = "2026-09-16T20:00:00Z"
        result = evaluate_action_witness(BASE_CONTRACT, BASE_PROOF, BASE_ACTION, corroboration)
        self.assertEqual(result["classification"], "TEMPORAL_UNCERTAIN")

    def test_open_gate_is_reported_without_authorizing_action(self) -> None:
        proof = copy.deepcopy(BASE_PROOF)
        proof["gate_state"] = "OPEN"
        proof["proof_state"] = "VALID"
        result = evaluate_action_witness(BASE_CONTRACT, proof, BASE_ACTION, BASE_CORROBORATION)
        self.assertEqual(result["classification"], "PRE_ACTION_OPEN_CORROBORATED")
        self.assertEqual(result["authority"], "OBSERVATIONAL_ONLY")

    def test_naive_timestamp_is_rejected(self) -> None:
        proof = copy.deepcopy(BASE_PROOF)
        proof["evaluated_at"] = "2026-09-16T19:22:02"
        with self.assertRaises(WitnessError):
            evaluate_action_witness(BASE_CONTRACT, proof, BASE_ACTION, BASE_CORROBORATION)

    def test_contract_owns_binding_law(self) -> None:
        proof = copy.deepcopy(BASE_PROOF)
        proof["direct_subject_keys"] = ["source_head_sha"]  # ignored producer suggestion
        result = evaluate_action_witness(BASE_CONTRACT, proof, BASE_ACTION, BASE_CORROBORATION)
        self.assertEqual(result["subject_binding"]["direct"]["matched"], BASE_CONTRACT["direct_subject_keys"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
