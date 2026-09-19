#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from proof_spine_obligation_memory import ObligationError, evaluate_obligation_memory


CONTRACT = {
    "schema_version": 1,
    "kind": "FCMO_PROOF_SPINE_OBLIGATION_CONTRACT",
    "project": {"id": "newsletter", "repository": "FCMO-AI/FCMO-AI-Newsletter"},
    "identity_keys": ["research_id", "required_locales"],
    "open_states": ["MISSING"],
    "resolved_states": ["COMPLETE"],
}


def snapshot(at: str, observations: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_OBLIGATION_SNAPSHOT",
        "authority": "EVIDENCE_ONLY",
        "project": CONTRACT["project"],
        "observed_at": at,
        "observations": observations,
    }


def missing() -> dict:
    return {
        "subject": {"research_id": "FCMO-7EBD0FA07C12", "required_locales": ["es-419", "zh-Hans"]},
        "state": "MISSING",
    }


class ObligationMemoryTests(unittest.TestCase):
    def test_absence_does_not_age_open_debt_to_resolved(self) -> None:
        result = evaluate_obligation_memory(
            CONTRACT,
            [snapshot("2026-09-16T21:23:20Z", [missing()]), snapshot("2026-09-17T00:37:08Z", [])],
        )
        self.assertEqual(result["summary"], {"active": 1, "resolved": 0, "total_known": 1})
        self.assertEqual(result["obligations"][0]["state"], "ACTIVE")
        self.assertEqual(result["transitions"][-1]["event"], "ABSENT_BUT_CARRIED_OPEN")

    def test_explicit_resolution_closes_known_debt(self) -> None:
        closed = missing()
        closed["state"] = "COMPLETE"
        result = evaluate_obligation_memory(
            CONTRACT,
            [snapshot("2026-09-16T21:23:20Z", [missing()]), snapshot("2026-09-17T00:37:08Z", [closed])],
        )
        self.assertEqual(result["summary"]["resolved"], 1)
        self.assertTrue(result["obligations"][0]["closure_evidence"])

    def test_orphan_resolution_does_not_manufacture_known_history(self) -> None:
        closed = missing()
        closed["state"] = "COMPLETE"
        result = evaluate_obligation_memory(CONTRACT, [snapshot("2026-09-17T00:37:08Z", [closed])])
        self.assertEqual(result["summary"]["total_known"], 0)
        self.assertEqual(result["transitions"][0]["event"], "ORPHAN_RESOLUTION_IGNORED")

    def test_reopened_debt_increments_generation(self) -> None:
        closed = missing()
        closed["state"] = "COMPLETE"
        result = evaluate_obligation_memory(
            CONTRACT,
            [
                snapshot("2026-09-16T20:00:00Z", [missing()]),
                snapshot("2026-09-16T21:00:00Z", [closed]),
                snapshot("2026-09-16T22:00:00Z", [missing()]),
            ],
        )
        self.assertEqual(result["obligations"][0]["generation"], 2)
        self.assertEqual(result["obligations"][0]["state"], "ACTIVE")
        self.assertEqual(result["obligations"][0]["opened_at"], "2026-09-16T22:00:00+00:00")

    def test_repeated_open_observation_does_not_rejuvenate_debt_age(self) -> None:
        result = evaluate_obligation_memory(
            CONTRACT,
            [
                snapshot("2026-09-16T20:00:00Z", [missing()]),
                snapshot("2026-09-17T20:00:00Z", [missing()]),
            ],
        )
        obligation = result["obligations"][0]
        self.assertEqual(obligation["opened_at"], "2026-09-16T20:00:00+00:00")
        self.assertEqual(obligation["last_seen_at"], "2026-09-17T20:00:00+00:00")
        self.assertEqual(obligation["generation"], 1)

    def test_reviewed_contract_can_require_resolution_measurement_evidence(self) -> None:
        contract = copy.deepcopy(CONTRACT)
        contract["resolution_evidence_required"] = True
        closed = missing()
        closed["state"] = "COMPLETE"
        with self.assertRaises(ObligationError):
            evaluate_obligation_memory(
                contract,
                [
                    snapshot("2026-09-16T20:00:00Z", [missing()]),
                    snapshot("2026-09-16T21:00:00Z", [closed]),
                ],
            )

        closed["resolution_evidence"] = {
            "observed_at": "2026-09-16T20:59:30Z",
            "evidence_refs": ["newsletter-release-validator:run-123"],
            "measurement_roots": ["newsletter:strict-localization-release-gate"],
        }
        result = evaluate_obligation_memory(
            contract,
            [
                snapshot("2026-09-16T20:00:00Z", [missing()]),
                snapshot("2026-09-16T21:00:00Z", [closed]),
            ],
        )
        obligation = result["obligations"][0]
        self.assertEqual(obligation["state"], "RESOLVED")
        self.assertTrue(obligation["closure_evidence"])
        self.assertEqual(
            obligation["closure_evidence_refs"],
            ["newsletter-release-validator:run-123"],
        )
        self.assertEqual(
            obligation["closure_measurement_roots"],
            ["newsletter:strict-localization-release-gate"],
        )
        self.assertTrue(obligation["closure_evidence_digest"].startswith("sha256:"))

    def test_resolution_evidence_cannot_come_from_the_future(self) -> None:
        contract = copy.deepcopy(CONTRACT)
        contract["resolution_evidence_required"] = True
        closed = missing()
        closed["state"] = "COMPLETE"
        closed["resolution_evidence"] = {
            "observed_at": "2026-09-16T22:00:00Z",
            "evidence_refs": ["future-proof"],
            "measurement_roots": ["future-root"],
        }
        with self.assertRaises(ObligationError):
            evaluate_obligation_memory(
                contract,
                [
                    snapshot("2026-09-16T20:00:00Z", [missing()]),
                    snapshot("2026-09-16T21:00:00Z", [closed]),
                ],
            )

    def test_unknown_state_cannot_close_active_debt(self) -> None:
        weird = missing()
        weird["state"] = "HEALTHY"
        result = evaluate_obligation_memory(
            CONTRACT,
            [snapshot("2026-09-16T20:00:00Z", [missing()]), snapshot("2026-09-16T21:00:00Z", [weird])],
        )
        self.assertEqual(result["summary"]["active"], 1)
        self.assertEqual(result["transitions"][-1]["event"], "UNKNOWN_STATE_CARRIED_OPEN")

    def test_producer_cannot_change_resolution_vocabulary(self) -> None:
        fake = snapshot("2026-09-16T21:00:00Z", [missing()])
        fake["resolved_states"] = ["MISSING"]
        result = evaluate_obligation_memory(CONTRACT, [fake])
        self.assertEqual(result["summary"]["active"], 1)

    def test_project_mismatch_is_rejected(self) -> None:
        wrong = snapshot("2026-09-16T21:00:00Z", [missing()])
        wrong["project"] = {"id": "other", "repository": "x/y"}
        with self.assertRaises(ObligationError):
            evaluate_obligation_memory(CONTRACT, [wrong])

    def test_naive_snapshot_time_is_rejected(self) -> None:
        with self.assertRaises(ObligationError):
            evaluate_obligation_memory(CONTRACT, [snapshot("2026-09-16T21:00:00", [missing()])])


if __name__ == "__main__":
    unittest.main(verbosity=2)
