#!/usr/bin/env python3
"""Adversarial tests for hardened FCMO Proof Spine v0.2."""
from __future__ import annotations
import importlib.util, json, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("proof_spine_v2", HERE / "proof_spine_v2.py")
mod = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = mod; SPEC.loader.exec_module(mod)
NOW_FRESH = datetime(2026, 9, 14, 18, tzinfo=timezone.utc)
NOW_EXACT_EXPIRY = datetime(2026, 9, 15, 12, tzinfo=timezone.utc)
NOW_STALE = datetime(2026, 9, 16, 0, tzinfo=timezone.utc)

def proofspec(rule_mid=None):
    return {
        "schema_version": 2,
        "mission": {"objective": "Keep production current", "context": {"environment": "production"}},
        "claims": [
            {"id": "upstream_fresh", "rule": {"all": ["arb"]}},
            {"id": "release_valid", "rule": {"all": ["upstream_fresh", "release"]}},
            {"id": "live_verified", "rule": {"all": ["release_valid", "browser"]}},
            {"id": "publishable", "rule": rule_mid or {"all": ["live_verified"]}},
        ],
        "gates": [{"id": "advance_current", "action": "advance current edition", "behavior": "block_unless_valid", "rule": {"all": ["publishable"]}}],
    }

def envelope():
    return {
        "schema_version": 2,
        "evidence": [
            {"id": "arb", "status": "OBSERVED", "observed_at": "2026-09-14T12:00:00Z", "max_age_hours": 24, "applies_to": {"environment": "production"}, "causal_root": "arb-snapshot-2026-09-14"},
            {"id": "release", "status": "PASS", "causal_root": "release-gates"},
            {"id": "browser", "status": "PASS", "causal_root": "live-browser"},
        ],
    }

def evaluate(ps=None, ev=None, now=NOW_FRESH, root=HERE):
    return mod.evaluate(ps or proofspec(), ev or envelope(), now, root)

def expect_error(fn, contains):
    try: fn()
    except mod.ProofError as exc:
        assert contains in str(exc), (contains, str(exc)); return
    raise AssertionError(f"expected ProofError containing {contains!r}")

def test_fresh_opens_gate():
    r = evaluate(); assert r["gates"]["advance_current"]["state"] == "OPEN"

def test_stale_cascades_and_closes_gate():
    r = evaluate(now=NOW_STALE)
    assert r["evidence"]["arb"]["state"] == "STALE"
    for cid in ("upstream_fresh", "release_valid", "live_verified", "publishable"):
        assert r["claims"][cid]["state"] == "STALE"
        assert "arb" in r["claims"][cid]["terminal_causes"]
    assert r["gates"]["advance_current"]["state"] == "CLOSED"
    assert "gate:advance_current" in r["blast_radius"]["arb"]["effective_current_impact"]

def test_exact_expiry_is_stale():
    assert evaluate(now=NOW_EXACT_EXPIRY)["evidence"]["arb"]["state"] == "STALE"

def test_unrelated_stale_does_not_close_gate():
    ev = envelope(); ev["evidence"].append({"id":"unrelated","status":"STALE","causal_root":"unrelated"})
    r = evaluate(ev=ev)
    assert r["gates"]["advance_current"]["state"] == "OPEN"
    assert r["blast_radius"]["unrelated"]["structural_descendants"] == []
    assert "unrelated" in r["coverage"]["unused_evidence"]

def test_any_valid_alternative_masks_stale_branch():
    ps = proofspec({"any": ["live_verified", "manual_override"]})
    ps["claims"].append({"id":"manual_override","rule":{"all":["override_ev"]}})
    ev = envelope(); ev["evidence"].append({"id":"override_ev","status":"APPROVED","causal_root":"human-override"})
    assert evaluate(ps, ev, now=NOW_STALE)["gates"]["advance_current"]["state"] == "OPEN"

def test_at_least_threshold():
    ps = proofspec({"at_least":{"count":2,"of":["live_verified","alt1","alt2"]}})
    ps["claims"] += [{"id":"alt1","rule":{"all":["a1"]}}, {"id":"alt2","rule":{"all":["a2"]}}]
    ev = envelope(); ev["evidence"] += [{"id":"a1","status":"PASS","causal_root":"r1"},{"id":"a2","status":"FAIL","causal_root":"r2"}]
    assert evaluate(ps, ev)["gates"]["advance_current"]["state"] == "OPEN"

def test_independent_threshold_rejects_duplicate_causal_roots():
    ps = proofspec({"all":["quorum"]})
    ps["claims"].append({"id":"quorum","rule":{"at_least":{"count":2,"of":["q1","q2"],"independent":True}}})
    ev = envelope(); ev["evidence"] += [
        {"id":"q1","status":"PASS","causal_root":"same-report"},
        {"id":"q2","status":"PASS","causal_root":"same-report"},
    ]
    r = evaluate(ps, ev)
    assert r["claims"]["quorum"]["state"] == "INVALID"
    assert r["gates"]["advance_current"]["state"] == "CLOSED"
    assert r["gates"]["advance_current"]["structural_repair_required"] is True

def test_independent_threshold_accepts_distinct_roots():
    ps = proofspec({"all":["quorum"]})
    ps["claims"].append({"id":"quorum","rule":{"at_least":{"count":2,"of":["q1","q2"],"independent":True}}})
    ev = envelope(); ev["evidence"] += [
        {"id":"q1","status":"PASS","causal_root":"report-a"},
        {"id":"q2","status":"PASS","causal_root":"report-b"},
    ]
    assert evaluate(ps, ev)["gates"]["advance_current"]["state"] == "OPEN"

def test_independent_threshold_requires_causal_root():
    ps = proofspec({"all":["quorum"]})
    ps["claims"].append({"id":"quorum","rule":{"at_least":{"count":2,"of":["q1","q2"],"independent":True}}})
    ev = envelope(); ev["evidence"] += [{"id":"q1","status":"PASS"},{"id":"q2","status":"PASS","causal_root":"b"}]
    expect_error(lambda: evaluate(ps, ev), "needs causal_root")

def test_cycle_rejected():
    ps = proofspec(); ps["claims"][0]["rule"] = {"all":["publishable"]}
    expect_error(lambda: evaluate(ps), "cycle")

def test_unknown_dependency_rejected():
    ps = proofspec(); ps["claims"][0]["rule"] = {"all":["ghost"]}
    expect_error(lambda: evaluate(ps), "unknown dependencies")

def test_runtime_cannot_rewrite_contract():
    ev = envelope(); ev["gates"] = []
    expect_error(lambda: evaluate(ev=ev), "contract fields")

def test_context_mismatch_invalidates():
    ev = envelope(); ev["evidence"][0]["applies_to"] = {"environment":"staging"}
    assert evaluate(ev=ev)["gates"]["advance_current"]["state"] == "CLOSED"

def test_unknown_fails_closed():
    ev = envelope(); ev["evidence"][0]["status"] = "PENDING"
    r = evaluate(ev=ev)
    assert r["claims"]["publishable"]["state"] == "UNKNOWN"
    assert r["gates"]["advance_current"]["state"] == "CLOSED"

def test_local_hash_binding():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); (root/"artifact.txt").write_text("hello")
        ev = envelope(); ev["evidence"][0] = {"id":"arb","status":"PASS","locator":"file:artifact.txt","sha256":"0"*64,"causal_root":"artifact"}
        assert evaluate(ev=ev, root=root)["evidence"]["arb"]["state"] == "INVALID"

def test_contract_and_evidence_have_independent_digests():
    a = evaluate(); ps = proofspec(); ps["mission"]["objective"] += " safely"; b = evaluate(ps=ps)
    assert a["proofspec_digest"] != b["proofspec_digest"]
    assert a["evidence_digest"] == b["evidence_digest"]

def test_next_gate_recheck_is_exact_expiry():
    r = evaluate()
    assert r["temporal"]["next_gate_recheck_at"] == "2026-09-15T12:00:00+00:00"
    assert r["evidence"]["arb"]["next_transition_at"] == "2026-09-15T12:00:00+00:00"

def test_repair_frontier_for_all_chain_is_single_terminal():
    r = evaluate(now=NOW_STALE)
    assert r["gates"]["advance_current"]["minimal_repair_sets"] == [["arb"]]
    assert r["gates"]["advance_current"]["repair_frontier"] == ["arb"]

def test_any_repair_frontier_returns_alternatives():
    ps = proofspec({"any":["live_verified","manual_override"]})
    ps["claims"].append({"id":"manual_override","rule":{"all":["override_ev"]}})
    ev = envelope(); ev["evidence"].append({"id":"override_ev","status":"PENDING","causal_root":"human-override"})
    r = evaluate(ps, ev, now=NOW_STALE)
    repairs = {tuple(x) for x in r["gates"]["advance_current"]["minimal_repair_sets"]}
    assert repairs == {("arb",), ("override_ev",)}

def test_all_repair_frontier_requires_both_terminals():
    ev = envelope(); ev["evidence"][0]["status"] = "FAIL"; ev["evidence"][1]["status"] = "FAIL"
    r = evaluate(ev=ev)
    assert r["gates"]["advance_current"]["minimal_repair_sets"] == [["arb","release"]]

def test_counterfactual_changes_only_copy():
    env = envelope(); baseline = evaluate(ev=env)
    scenario_env = mod.apply_assumptions(env, {"arb":"STALE"})
    scenario = evaluate(ev=scenario_env)
    delta = mod.state_delta(baseline, scenario)
    assert env["evidence"][0]["status"] == "OBSERVED"
    assert delta["gates"]["advance_current"] == {"from":"OPEN","to":"CLOSED"}
    assert delta["claims"]["publishable"] == {"from":"VALID","to":"STALE"}

def test_unknown_counterfactual_id_rejected():
    expect_error(lambda: mod.apply_assumptions(envelope(), {"ghost":"FAIL"}), "unknown evidence ids")

def test_repair_frontier_never_silently_truncates():
    refs = [f"e{i}" for i in range(mod.MAX_REPAIR_SETS + 1)]
    ps = {
        "schema_version": 2,
        "mission": {"objective": "bounded repair truth", "context": {}},
        "claims": [{"id":"route","rule":{"any":refs}}],
        "gates": [{"id":"g","action":"x","behavior":"block_unless_valid","rule":{"all":["route"]}}],
    }
    ev = {"schema_version":2,"evidence":[{"id":r,"status":"FAIL","causal_root":r} for r in refs]}
    expect_error(lambda: evaluate(ps, ev), "repair frontier exceeds")

def test_ungated_claim_is_visible_in_coverage():
    ps = proofspec(); ps["claims"].append({"id":"diagnostic_only","rule":{"all":["browser"]}})
    assert "diagnostic_only" in evaluate(ps=ps)["coverage"]["ungated_claims"]

TESTS = [v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
if __name__ == "__main__":
    failed = 0
    for test in TESTS:
        try: test(); print(f"PASS {test.__name__}")
        except Exception as exc: failed += 1; print(f"FAIL {test.__name__}: {exc}")
    print(f"{len(TESTS)-failed}/{len(TESTS)} tests passed")
    raise SystemExit(1 if failed else 0)
