#!/usr/bin/env python3
"""Adversarial tests for tools/proof_spine.py."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("proof_spine.py")
spec = importlib.util.spec_from_file_location("proof_spine", MODULE_PATH)
proof_spine = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = proof_spine
spec.loader.exec_module(proof_spine)

NOW = datetime(2026, 9, 14, 20, 0, tzinfo=timezone.utc)


class ProofSpineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        artifact = self.root / "result.txt"
        artifact.write_text("verified output\n", encoding="utf-8")
        self.digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def valid_payload(self) -> dict:
        return {
            "schema_version": 1,
            "mission": {"objective": "Ship a verified improvement without overstating what was proven."},
            "evidence": [
                {"id": "E-art", "kind": "artifact", "locator": "file:result.txt", "sha256": self.digest},
                {"id": "E-run", "kind": "test", "locator": "pytest::suite", "status": "PASS", "observed_at": "2026-09-14T19:50:00Z", "max_age_hours": 2},
                {"id": "E-bench", "kind": "benchmark", "locator": "bench::v1", "status": "PASS", "comparison": "+18% throughput vs baseline"},
                {"id": "E-auth", "kind": "user_instruction", "locator": "conversation::explicit-authority"},
            ],
            "claims": [
                {"id": "C-fact", "statement": "The output artifact exists with the recorded bytes.", "type": "fact", "materiality": "material", "boundary": "Only the local artifact bytes are proven.", "evidence": ["E-art"]},
                {"id": "C-exec", "statement": "The relevant test suite executed successfully.", "type": "execution", "materiality": "material", "boundary": "Only the cited suite status is claimed.", "evidence": ["E-run"]},
                {"id": "C-perf", "statement": "Throughput improved against the declared baseline.", "type": "performance", "materiality": "critical", "boundary": "Only the recorded benchmark regime is covered.", "evidence": ["E-bench"]},
                {"id": "C-done", "statement": "The bounded acceptance target is complete.", "type": "completion", "materiality": "material", "boundary": "Completion is limited to the listed criterion.", "acceptance_criteria": "Artifact exists and cited test passes.", "evidence": ["E-run", "E-art"]},
                {"id": "C-fresh", "statement": "The execution evidence is still current for this decision.", "type": "freshness", "materiality": "material", "boundary": "Current only inside the two-hour window.", "evidence": ["E-run"]},
                {"id": "C-auth", "statement": "The work is within explicit user authority.", "type": "authority", "materiality": "critical", "boundary": "Authority is limited to the cited instruction.", "evidence": ["E-auth"]},
            ],
        }

    def codes(self, payload: dict) -> set[str]:
        return {issue.code for issue in proof_spine.validate_receipt(payload, self.root, NOW) if issue.level == "ERROR"}

    def test_valid_receipt_passes(self) -> None:
        self.assertEqual(self.codes(self.valid_payload()), set())

    def test_attempt_cannot_prove_execution(self) -> None:
        payload = self.valid_payload()
        payload["evidence"].append({"id": "E-attempt", "kind": "attempt", "locator": "job::queued"})
        payload["claims"][1]["evidence"] = ["E-attempt"]
        self.assertIn("EXECUTION_NOT_PROVEN", self.codes(payload))

    def test_missing_reference_fails(self) -> None:
        payload = self.valid_payload()
        payload["claims"][0]["evidence"] = ["E-does-not-exist"]
        self.assertIn("UNKNOWN_EVIDENCE_REF", self.codes(payload))

    def test_stale_evidence_cannot_prove_freshness(self) -> None:
        payload = self.valid_payload()
        payload["evidence"][1]["observed_at"] = "2026-09-13T19:00:00Z"
        codes = self.codes(payload)
        self.assertIn("STALE_EVIDENCE", codes)
        self.assertIn("FRESHNESS_NOT_PROVEN", codes)

    def test_authority_needs_authority_evidence(self) -> None:
        payload = self.valid_payload()
        payload["claims"][-1]["evidence"] = ["E-art"]
        self.assertIn("AUTHORITY_NOT_PROVEN", self.codes(payload))

    def test_hash_mismatch_fails(self) -> None:
        payload = self.valid_payload()
        payload["evidence"][0]["sha256"] = "0" * 64
        self.assertIn("SHA256_MISMATCH", self.codes(payload))

    def test_material_claim_needs_boundary(self) -> None:
        payload = self.valid_payload()
        payload["claims"][0].pop("boundary")
        self.assertIn("CLAIM_BOUNDARY_MISSING", self.codes(payload))

    def test_performance_needs_explicit_comparison(self) -> None:
        payload = self.valid_payload()
        payload["evidence"][2].pop("comparison")
        self.assertIn("PERFORMANCE_COMPARISON_MISSING", self.codes(payload))


# Footnote for future maintainers: these tests intentionally attack seductive failure
# modes ("we tried it" => "it ran", old evidence => "current", artifact => authority,
# benchmark without baseline => performance). Add new tests when a real FCMO incident
# reveals another route by which plausible metadata could launder an unsupported claim.


if __name__ == "__main__":
    unittest.main()
