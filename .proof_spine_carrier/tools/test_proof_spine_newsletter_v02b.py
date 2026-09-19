#!/usr/bin/env python3
"""Field-semantics tests for the Newsletter Proof Spine v0.2b correction."""
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
EVIDENCE_PATH = ROOT / "commons/experiments/2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_EVIDENCE_v0.2b.json"

SPEC = importlib.util.spec_from_file_location("proof_spine_v2", HERE / "proof_spine_v2.py")
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

NOW = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
EXACT_CANDIDATE_FRESHNESS_EXPIRY = datetime(2026, 9, 15, 2, tzinfo=timezone.utc)


def load_payloads():
    return json.loads(SPEC_PATH.read_text()), json.loads(EVIDENCE_PATH.read_text())


def set_status(envelope, evidence_id, status):
    for item in envelope["evidence"]:
        if item["id"] == evidence_id:
            item["status"] = status
            return
    raise AssertionError(f"missing evidence id {evidence_id}")


# Footnote for future maintainers: this is the regression that motivated v0.2b.
# A candidate that never deployed must fail closed for candidate advancement, but it
# must not manufacture a live-site incident when independent known-good health proof
# remains valid. Keep these two gates causally separate unless Newsletter law changes.
def test_skipped_candidate_closes_candidate_gate_only():
    proofspec, evidence = load_payloads()
    result = mod.evaluate(proofspec, evidence, NOW, ROOT)

    candidate = result["gates"]["advance_candidate_current_edition"]
    live = result["gates"]["represent_live_production_healthy"]

    assert candidate["state"] == "CLOSED"
    assert candidate["proof_state"] == "UNKNOWN"
    assert candidate["minimal_repair_sets"] == [[
        "candidate_pages_deploy",
        "candidate_post_deploy_browser",
        "candidate_triggered_health",
    ]]
    assert live["state"] == "OPEN"
    assert live["proof_state"] == "VALID"


# Footnote: isolation must work in both directions. A live known-good health failure
# may close the health representation gate without retroactively erasing otherwise
# valid evidence that a newly deployed candidate completed its own advancement proof.
def test_live_health_failure_does_not_retroactively_poison_candidate():
    proofspec, baseline = load_payloads()
    evidence = copy.deepcopy(baseline)
    set_status(evidence, "candidate_pages_deploy", "PASS")
    set_status(evidence, "candidate_post_deploy_browser", "PASS")
    set_status(evidence, "candidate_triggered_health", "PASS")
    set_status(evidence, "live_serving_probe", "FAIL")

    result = mod.evaluate(proofspec, evidence, NOW, ROOT)
    assert result["gates"]["advance_candidate_current_edition"]["state"] == "OPEN"
    assert result["gates"]["represent_live_production_healthy"]["state"] == "CLOSED"
    assert result["gates"]["represent_live_production_healthy"]["proof_state"] == "INVALID"


# Footnote: time-driven invalidation is branch-local too. Expiring candidate research
# proof closes candidate advancement at the exact deadline while independent live
# health remains valid; freshness must not become a global kill switch by accident.
def test_candidate_freshness_expiry_is_branch_local():
    proofspec, evidence = load_payloads()
    set_status(evidence, "candidate_pages_deploy", "PASS")
    set_status(evidence, "candidate_post_deploy_browser", "PASS")
    set_status(evidence, "candidate_triggered_health", "PASS")

    result = mod.evaluate(proofspec, evidence, EXACT_CANDIDATE_FRESHNESS_EXPIRY, ROOT)
    assert result["evidence"]["candidate_arb_public_safe"]["state"] == "STALE"
    assert result["gates"]["advance_candidate_current_edition"]["state"] == "CLOSED"
    assert result["gates"]["advance_candidate_current_edition"]["proof_state"] == "STALE"
    assert result["gates"]["represent_live_production_healthy"]["state"] == "OPEN"


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
