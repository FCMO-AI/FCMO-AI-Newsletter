#!/usr/bin/env python3
"""Adversarial tests for the federated Newsletter Proof Spine shadow adapter."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC_PATH = ROOT / "commons/experiments/2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_PROOFSPEC_v0.2b.json"

SPEC = importlib.util.spec_from_file_location("proof_spine_newsletter_shadow", HERE / "proof_spine_newsletter_shadow.py")
shadow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = shadow
SPEC.loader.exec_module(shadow)

PROOFSPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
OBSERVED = datetime(2026, 9, 14, 23, 52, 15, tzinfo=timezone.utc)


def healthy_receipt():
    return {
        "schema_version": 1,
        "kind": "FCMO_NEWSLETTER_PRODUCTION_HEALTH_SHADOW_RECEIPT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "observed_at": "2026-09-14T23:52:15Z",
        "source": {
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "head_sha": "shadow-head",
            "branch": "agent/proof-spine-shadow-pilot",
            "workflow_run_id": "34910748578",
            "main_sha_at_observation": "main-head",
        },
        "source_alignment": {
            "state": "MATCH",
            "before": {"state": "MATCH", "main_sha": "main-head", "material_paths_match_main": True, "drifted_paths": []},
            "after": {"state": "MATCH", "main_sha": "main-head", "material_paths_match_main": True, "drifted_paths": []},
        },
        "local_surface": {"state": "HEALTHY", "quality_state": "HEALTHY"},
        "source_facts": {
            "airlock_generated_at": "2026-09-14T19:35:00Z",
            "newsroom_finalized_at": "2026-09-14T19:38:00Z",
            "lead": {"research_id": "FCMO-FAD9D0AFD3E4", "timestamp": "2026-09-14T02:48:00Z", "importance": 5},
            "newest_material": {"research_id": "FCMO-FAD9D0AFD3E4", "timestamp": "2026-09-14T02:48:00Z", "importance": 5},
        },
        "upstream_publication": {
            "state": "MATCH",
            "seal_state": "SEALED",
            "semantic_material_delta": False,
            "upstream": {"corpus_digest": "digest-a", "release_id": "newswire-digest-a", "record_count": 42},
            "newsletter_corpus": {"corpus_digest": "digest-a", "release_id": "newswire-digest-a", "record_count": 42},
            "delta": {
                "added_public_ids": [],
                "changed_public_ids": [],
                "removed_public_ids": [],
                "material_public_ids": [],
            },
        },
        "checks": {
            "serving_health": {"status": "PASS", "structured_output": None},
            "surface_oracle": {"status": "PASS", "structured_output": None},
            "publication_freshness": {"status": "PASS", "structured_output": None},
            "editorial_freshness": {
                "status": "PASS",
                "structured_output": {"state": "HEALTHY", "stage": "EDITORIAL_FRESHNESS"},
            },
            "translation_health": {
                "status": "PASS",
                "structured_output": {"state": "HEALTHY", "stage": "TRANSLATION_HEALTH"},
            },
        },
    }


def evidence_by_id(envelope, evidence_id):
    return next(item for item in envelope["evidence"] if item["id"] == evidence_id)


# Footnote for future maintainers: this is the prospective specificity baseline. A
# healthy Newsletter-local heartbeat must stay healthy in shadow while the unrelated
# candidate-advancement branch remains unproven rather than being inferred from live
# known-good health.
def test_healthy_shadow_agrees_without_promoting_candidate():
    receipt = healthy_receipt()
    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_HEALTHY"
    assert report["proof_spine_live_gate"]["state"] == "OPEN"
    assert report["proof_spine_live_decision_receipt"]["kind"] == "FCMO_PROOF_SPINE_DECISION_RECEIPT"
    assert report["proof_spine_live_decision_receipt_digest"] == shadow.federation.canonical_sha256(
        report["proof_spine_live_decision_receipt"]
    )
    assert report["proof_spine_predeploy_decision_receipt"]["kind"] == "FCMO_PROOF_SPINE_DECISION_RECEIPT"
    assert report["proof_spine_predeploy_decision_receipt_digest"] == shadow.federation.canonical_sha256(
        report["proof_spine_predeploy_decision_receipt"]
    )
    # Footnote: the adapter must preserve at least one concrete semantic identity key
    # inside the receipt context so calibration cannot relabel a real decision onto a
    # different Newsletter subject. This is a legacy v1 shadow receipt, so its reviewed
    # identity is the historical branch head; v2 source-aligned candidate receipts bind
    # to candidate_source_sha/main instead.
    assert report["proof_spine_live_decision_receipt"]["context"]["source_sha"] == "shadow-head"
    assert report["candidate_gate_observational_only"]["state"] == "CLOSED"
    assert report["candidate_gate_observational_only"]["proof_state"] == "UNKNOWN"
    assert report["upstream_material_sync_signal"] == "UPSTREAM_MATERIAL_SYNCED"
    assert report["upstream_material_sync_gate"]["state"] == "OPEN"
    assert report["next_quality_transition_at"] == "2026-09-15T02:48:00.000001Z"
    assert report["proof_spine_next_gate_recheck_at"] == "2026-09-16T01:35:00.000001Z"


# Footnote: the local editorial checker checks Airlock before editorial Story health.
# If that prerequisite is the positive failure, shadow normalization must not invent
# a second editorial failure. UNKNOWN means "not established after prerequisite fail".
def test_airlock_failure_is_not_double_counted_as_editorial_failure():
    receipt = healthy_receipt()
    receipt["local_surface"] = {"state": "UNHEALTHY", "quality_state": "UNHEALTHY"}
    receipt["checks"]["publication_freshness"]["status"] = "FAIL"
    receipt["checks"]["editorial_freshness"] = {
        "status": "FAIL",
        "structured_output": {"state": "UNHEALTHY", "stage": "AIRLOCK"},
    }

    envelope = shadow.build_envelope(receipt)
    assert evidence_by_id(envelope, "live_airlock_freshness")["status"] == "FAIL"
    assert evidence_by_id(envelope, "live_editorial_freshness")["status"] == "UNKNOWN"

    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_UNHEALTHY"
    assert report["proof_spine_live_gate"]["state"] == "CLOSED"
    assert report["proof_spine_live_gate"]["proof_state"] == "INVALID"
    assert report["proof_spine_live_gate"]["terminal_causes"] == ["live_airlock_freshness"]


# Footnote: DEGRADED_ACCEPTABLE is project-local quality nuance, not a fifth generic
# Proof Spine truth state. Preserve it alongside an OPEN acceptability gate rather
# than bloating the shared state machine or falsely calling it unhealthy.
def test_degraded_acceptable_preserves_quality_nuance():
    receipt = healthy_receipt()
    receipt["local_surface"]["quality_state"] = "DEGRADED_ACCEPTABLE"
    receipt["checks"]["editorial_freshness"]["structured_output"]["state"] = "DEGRADED_ACCEPTABLE"
    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_HEALTHY"
    assert report["local_surface"]["quality_state"] == "DEGRADED_ACCEPTABLE"
    assert report["proof_spine_live_gate"]["state"] == "OPEN"
    assert report["next_quality_transition_at"] is None


# Footnote: missing execution is epistemic absence, not positive failure. The shadow
# must therefore fail closed as UNKNOWN and never upgrade an incomplete receipt into
# a healthy representation.
def test_missing_live_check_stays_unknown_and_closed():
    receipt = healthy_receipt()
    receipt["local_surface"] = {"state": "UNKNOWN", "quality_state": "UNKNOWN"}
    del receipt["checks"]["surface_oracle"]
    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_UNPROVEN"
    assert report["proof_spine_live_gate"]["state"] == "CLOSED"
    assert report["proof_spine_live_gate"]["proof_state"] == "UNKNOWN"


# Footnote: a branch that has materially drifted from main may have executed every
# local check correctly while still being the wrong evidence source for current
# production. Preserve that as a positive applicability failure, not site failure.
def test_source_drift_closes_only_current_applicability():
    receipt = healthy_receipt()
    receipt["source_alignment"]["state"] = "DRIFTED"
    receipt["source_alignment"]["after"] = {
        "state": "DRIFTED",
        "main_sha": "new-main-head",
        "material_paths_match_main": False,
        "drifted_paths": ["site/data/stories.json"],
    }
    receipt["local_surface"] = {"state": "UNKNOWN", "quality_state": "UNKNOWN"}

    envelope = shadow.build_envelope(receipt)
    assert evidence_by_id(envelope, "live_source_alignment")["status"] == "FAIL"

    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_SOURCE_DRIFT"
    assert report["proof_spine_live_gate"]["state"] == "CLOSED"
    assert report["proof_spine_live_gate"]["proof_state"] == "INVALID"
    assert report["proof_spine_live_gate"]["terminal_causes"] == ["live_source_alignment"]


# Footnote: do not grandfather old receipts merely because they were once useful.
# A pre-alignment receipt remains historical evidence, but under the hardened contract
# it cannot establish current health until applicability to current main is proven.
def test_legacy_receipt_without_alignment_no_longer_proves_current_health():
    receipt = healthy_receipt()
    del receipt["source_alignment"]
    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "PROOF_SPINE_STRICTER"
    assert report["proof_spine_live_gate"]["state"] == "CLOSED"
    assert report["proof_spine_live_gate"]["proof_state"] == "UNKNOWN"
    assert report["next_quality_transition_at"] is None


# Footnote: keep the adapter aligned with the Newsletter's strict `age > threshold`
# semantics. Exactly 30h is still accepted locally; one microsecond later is stale.
def test_strict_threshold_boundary_matches_local_semantics():
    receipt = healthy_receipt()
    at_30h = datetime(2026, 9, 16, 1, 35, 0, tzinfo=timezone.utc)
    just_after = datetime(2026, 9, 16, 1, 35, 0, 1, tzinfo=timezone.utc)

    before = shadow.evaluate_shadow(PROOFSPEC, receipt, at_30h, ROOT)
    after = shadow.evaluate_shadow(PROOFSPEC, receipt, just_after, ROOT)
    assert before["proof_report"]["evidence"]["live_airlock_freshness"]["state"] == "VALID"
    assert after["proof_report"]["evidence"]["live_airlock_freshness"]["state"] == "STALE"


# Footnote: editorial expiry must not inherit Airlock's deadline. Those are separate
# proof nodes so a future Airlock expiry remains causally attributable to Airlock.
def test_editorial_deadline_excludes_airlock_dependency():
    receipt = healthy_receipt()
    envelope = shadow.build_envelope(receipt)
    editorial = evidence_by_id(envelope, "live_editorial_freshness")
    airlock = evidence_by_id(envelope, "live_airlock_freshness")
    assert airlock["valid_until"] == "2026-09-16T01:35:00.000001Z"
    assert editorial["valid_until"] == "2026-09-16T01:38:00.000001Z"


# Footnote: this is the critical causal-isolation regression for sensitivity. A
# material public ARB delta may prove Newsletter's ingested corpus is behind while the
# already-served site remains technically healthy. Only the narrow synchronization
# gate may close; serving/editorial/localization truth must not be poisoned.
def test_material_upstream_delta_closes_only_sync_gate():
    receipt = healthy_receipt()
    receipt["upstream_publication"] = {
        "state": "MATERIAL_PUBLIC_DELTA_AVAILABLE",
        "seal_state": "SEALED",
        "semantic_material_delta": True,
        "upstream": {"corpus_digest": "digest-b", "release_id": "newswire-digest-b", "record_count": 43},
        "newsletter_corpus": {"corpus_digest": "digest-a", "release_id": "newswire-digest-a", "record_count": 42},
        "delta": {
            "added_public_ids": ["FCMO-ABCDEF123456"],
            "changed_public_ids": [],
            "removed_public_ids": [],
            "material_public_ids": ["FCMO-ABCDEF123456"],
        },
    }

    envelope = shadow.build_envelope(receipt)
    assert evidence_by_id(envelope, "live_upstream_material_sync")["status"] == "FAIL"

    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_HEALTHY"
    assert report["proof_spine_live_gate"]["state"] == "OPEN"
    assert report["upstream_material_sync_signal"] == "UPSTREAM_MATERIAL_LAG"
    assert report["upstream_material_sync_gate"]["state"] == "CLOSED"
    assert report["upstream_material_sync_gate"]["proof_state"] == "INVALID"
    assert report["upstream_material_sync_gate"]["terminal_causes"] == ["live_upstream_material_sync"]


# Footnote: byte churn that does not change any importance>=4 public development is
# not enough to manufacture a consequential freshness incident. The semantic material
# synchronization claim remains valid while the receipt still exposes byte divergence.
def test_non_material_public_delta_does_not_fake_material_lag():
    receipt = healthy_receipt()
    receipt["upstream_publication"] = {
        "state": "NON_MATERIAL_PUBLIC_DELTA",
        "seal_state": "SEALED",
        "semantic_material_delta": False,
        "upstream": {"corpus_digest": "digest-b", "release_id": "newswire-digest-b", "record_count": 42},
        "newsletter_corpus": {"corpus_digest": "digest-a", "release_id": "newswire-digest-a", "record_count": 42},
        "delta": {
            "added_public_ids": [],
            "changed_public_ids": ["FCMO-LOWLOW123456"],
            "removed_public_ids": [],
            "material_public_ids": [],
        },
    }
    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["upstream_material_sync_signal"] == "UPSTREAM_MATERIAL_SYNCED"
    assert report["upstream_material_sync_gate"]["state"] == "OPEN"
    assert report["proof_spine_live_gate"]["state"] == "OPEN"


# Footnote: inability to seal current ARB main is not proof that Newsletter is behind.
# It is an epistemic boundary for the synchronization claim and must remain UNKNOWN
# without contaminating already-established live-health evidence.
def test_unsealable_upstream_is_unknown_not_site_failure():
    receipt = healthy_receipt()
    receipt["upstream_publication"] = {
        "state": "UNKNOWN",
        "seal_state": "CURRENT_MAIN_UNSEALABLE",
        "semantic_material_delta": None,
    }
    report = shadow.evaluate_shadow(PROOFSPEC, receipt, OBSERVED, ROOT)
    assert report["comparison"] == "AGREE_HEALTHY"
    assert report["proof_spine_live_gate"]["state"] == "OPEN"
    assert report["upstream_material_sync_signal"] == "UPSTREAM_SYNC_UNKNOWN"
    assert report["upstream_material_sync_gate"]["state"] == "CLOSED"
    assert report["upstream_material_sync_gate"]["proof_state"] == "UNKNOWN"


TESTS = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]

if __name__ == "__main__":
    failed = 0
    for test in TESTS:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"{len(TESTS) - failed}/{len(TESTS)} tests passed")
    raise SystemExit(1 if failed else 0)
