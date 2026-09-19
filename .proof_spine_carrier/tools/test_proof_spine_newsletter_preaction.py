#!/usr/bin/env python3
"""Prospective pre-action regressions for the Newsletter Proof Spine adapter."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LIVE_SPEC_PATH = ROOT / "commons/experiments/2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_PROOFSPEC_v0.2b.json"
FIELD_RECEIPT_PATH = ROOT / "commons/experiments/2026-09-16_FCMO_PROOF_SPINE_NEWSLETTER_PREACTION_RECEIPT_v0.2e.json"

SPEC = importlib.util.spec_from_file_location("proof_spine_newsletter_shadow_preaction", HERE / "proof_spine_newsletter_shadow.py")
shadow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = shadow
SPEC.loader.exec_module(shadow)

LIVE_SPEC = json.loads(LIVE_SPEC_PATH.read_text(encoding="utf-8"))


def healthy_v2_receipt() -> dict:
    """Construct a source-aligned receipt where live health and candidate law can differ."""
    return {
        "schema_version": 2,
        "kind": "FCMO_NEWSLETTER_PROOF_SPINE_SHADOW_RECEIPT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "observed_at": "2026-09-16T19:22:02Z",
        "source": {
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "head_sha": "experiment-head",
            "branch": "agent/proof-spine-preaction-shadow-v0.2e",
            "workflow_run_id": "field-preaction",
            "main_sha_at_observation": "main-candidate",
        },
        "source_alignment": {
            "state": "MATCH",
            "before": {"state": "MATCH", "main_sha": "main-candidate", "material_paths_match_main": True, "drifted_paths": []},
            "after": {"state": "MATCH", "main_sha": "main-candidate", "material_paths_match_main": True, "drifted_paths": []},
        },
        "candidate_release": {
            "candidate_source_sha": "main-candidate",
            "native_edition_observation": {
                "state": "INCOMPLETE_NATIVE_EDITIONS",
                "canonical_story_count": 43,
                "native_complete_story_count": 42,
                "pending_translation_count": 1,
                "pending_translation_ids": ["FCMO-7EBD0FA07C12"],
                "required_locales": ["es-419", "zh-Hans"],
                "source_oracle": "tools/validate_localizations_partial.py",
                "canonical_contract": "LOCALIZATION.md",
            },
            "six_release_gates": {"state": "NOT_OBSERVED"},
            "publication_authority": {"state": "NOT_OBSERVED"},
        },
        "local_surface": {"state": "HEALTHY", "quality_state": "HEALTHY"},
        "source_facts": {
            "airlock_generated_at": "2026-09-16T18:26:17Z",
            "newsroom_finalized_at": "2026-09-16T18:28:27Z",
            "lead": {"research_id": "FCMO-7EBD0FA07C12", "timestamp": "2026-09-16T18:30:00Z", "importance": 6},
            "newest_material": {"research_id": "FCMO-7EBD0FA07C12", "timestamp": "2026-09-16T18:30:00Z", "importance": 6},
        },
        "upstream_publication": {
            "state": "UNKNOWN",
            "seal_state": "NOT_OBSERVED",
            "semantic_material_delta": None,
        },
        "checks": {
            "serving_health": {"status": "PASS", "structured_output": None},
            "surface_oracle": {"status": "PASS", "structured_output": None},
            "publication_freshness": {"status": "PASS", "structured_output": None},
            "editorial_freshness": {"status": "PASS", "structured_output": {"state": "HEALTHY", "stage": "EDITORIAL_FRESHNESS"}},
            # Footnote: health grace and strict release eligibility are intentionally
            # different truths. This synthetic control represents a just-published Story
            # still inside health grace: live health can be green while strict candidate
            # completeness is already a release failure under LOCALIZATION.md.
            "translation_health": {"status": "PASS", "structured_output": {"state": "DEGRADED_TRANSLATION_GRACE", "stage": "TRANSLATION_HEALTH"}},
        },
    }


def evidence(report: dict, evidence_id: str) -> dict:
    return report["candidate_proof_report"]["evidence"][evidence_id]


# Footnote: historical v1 live-health receipts predate candidate observation. They must
# remain useful for live health while candidate localization is UNKNOWN, never retrofitted
# into PASS or FAIL from absence.
def test_legacy_receipt_keeps_candidate_localization_unknown():
    receipt = healthy_v2_receipt()
    receipt["schema_version"] = 1
    receipt["kind"] = "FCMO_NEWSLETTER_PRODUCTION_HEALTH_SHADOW_RECEIPT"
    del receipt["candidate_release"]
    report = shadow.evaluate_shadow(LIVE_SPEC, receipt, datetime(2026, 9, 16, 19, 22, 2, tzinfo=timezone.utc), ROOT)
    assert evidence(report, "candidate_localization_ready")["state"] == "UNKNOWN"
    assert report["proof_spine_predeploy_gate"]["state"] == "CLOSED"
    assert report["proof_spine_predeploy_gate"]["proof_state"] == "UNKNOWN"


# Footnote: this is the core prospective discriminator. A source-aligned candidate can
# be strictly invalid before deploy while the already-served live product remains healthy.
# Candidate failure must close only the candidate gate, never act as a global red switch.
def test_aligned_incomplete_candidate_closes_predeploy_without_poisoning_live_health():
    receipt = healthy_v2_receipt()
    report = shadow.evaluate_shadow(LIVE_SPEC, receipt, datetime(2026, 9, 16, 19, 22, 2, tzinfo=timezone.utc), ROOT)
    assert evidence(report, "candidate_localization_ready")["state"] == "INVALID"
    assert report["proof_spine_predeploy_gate"]["state"] == "CLOSED"
    assert report["proof_spine_predeploy_gate"]["proof_state"] == "INVALID"
    assert report["proof_spine_predeploy_signal"] == "CANDIDATE_WOULD_BE_BLOCKED_INVALID"
    assert report["proof_spine_live_gate"]["state"] == "OPEN"
    assert report["proof_spine_live_gate"]["proof_state"] == "VALID"


# Footnote: repairing the native editions alone does not create the independent six
# release gates or publication authority. COMPLETE raises one premise to PASS; the
# candidate remains CLOSED/UNKNOWN until its unknown siblings are actually observed.
def test_complete_localization_does_not_invent_release_authority():
    receipt = healthy_v2_receipt()
    native = receipt["candidate_release"]["native_edition_observation"]
    native.update({
        "state": "COMPLETE",
        "native_complete_story_count": 43,
        "pending_translation_count": 0,
        "pending_translation_ids": [],
    })
    report = shadow.evaluate_shadow(LIVE_SPEC, receipt, datetime(2026, 9, 16, 19, 22, 2, tzinfo=timezone.utc), ROOT)
    assert evidence(report, "candidate_localization_ready")["state"] == "VALID"
    assert report["proof_spine_predeploy_gate"]["state"] == "CLOSED"
    assert report["proof_spine_predeploy_gate"]["proof_state"] == "UNKNOWN"
    assert report["proof_spine_predeploy_signal"] == "CANDIDATE_WOULD_BE_BLOCKED_UNPROVEN"


# Footnote: a stale experiment branch is not evidence about current main. Even a local
# INCOMPLETE observation becomes UNKNOWN for the current candidate when source alignment
# is lost, preventing false accusations as well as false greens.
def test_source_drift_downgrades_candidate_observation_to_unknown():
    receipt = healthy_v2_receipt()
    receipt["source_alignment"]["state"] = "DRIFTED"
    receipt["source_alignment"]["after"] = {
        "state": "DRIFTED",
        "main_sha": "new-main",
        "material_paths_match_main": False,
        "drifted_paths": ["release-src"],
    }
    receipt["candidate_release"]["candidate_source_sha"] = None
    receipt["local_surface"] = {"state": "UNKNOWN", "quality_state": "UNKNOWN"}
    report = shadow.evaluate_shadow(LIVE_SPEC, receipt, datetime(2026, 9, 16, 19, 22, 2, tzinfo=timezone.utc), ROOT)
    assert evidence(report, "candidate_localization_ready")["state"] == "UNKNOWN"
    assert report["proof_spine_predeploy_gate"]["proof_state"] == "UNKNOWN"


# Footnote: preserve the real run-35140061610 facts as an executable field fixture.
# The canonical artifact remains separately identified by its ZIP + JSON SHA-256; this
# compact fixture intentionally keeps the public-safe facts the adapter needs rather
# than claiming byte identity with the downloaded artifact.
def test_field_fixture_would_close_predeploy_gate():
    receipt = json.loads(FIELD_RECEIPT_PATH.read_text(encoding="utf-8"))
    now = shadow.parse_time(receipt["observed_at"])
    report = shadow.evaluate_shadow(LIVE_SPEC, receipt, now, ROOT)
    assert report["source_alignment"]["state"] == "MATCH"
    assert evidence(report, "candidate_localization_ready")["state"] == "INVALID"
    assert report["proof_spine_predeploy_gate"]["state"] == "CLOSED"
    assert report["proof_spine_predeploy_gate"]["proof_state"] == "INVALID"
    assert report["proof_spine_predeploy_signal"] == "CANDIDATE_WOULD_BE_BLOCKED_INVALID"
    assert report["candidate_release"]["candidate_source_sha"] == "1af947d3be9f76ea963b4b293953dedb6729bb83"


TESTS = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]

if __name__ == "__main__":
    failures = 0
    for test in TESTS:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    raise SystemExit(1 if failures else 0)
