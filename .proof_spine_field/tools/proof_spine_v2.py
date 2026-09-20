#!/usr/bin/env python3
"""FCMO Proof Spine v0.2 — deterministic dependency invalidation engine.

A versioned proof contract is evaluated against a separate runtime evidence envelope.
If a premise becomes INVALID, STALE, or UNKNOWN, dependent claims are recomputed and
fail-closed gates close. The engine never performs the gated action itself.

This hardened v0.2 also exposes the smallest repair sets for closed gates, predicts
future time-driven invalidation, and supports side-effect-free counterfactuals.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2
VALID, INVALID, STALE, UNKNOWN = "VALID", "INVALID", "STALE", "UNKNOWN"
PASS = {"PASS", "VERIFIED", "OBSERVED", "APPROVED", "CURRENT"}
FAIL = {"FAIL", "FAILED", "REJECTED", "INVALID"}
UNK = {"UNKNOWN", "PENDING", "UNVERIFIED"}
OLD = {"STALE", "EXPIRED"}
MAX_REPAIR_SETS = 64

# Footnote for future maintainers: keep the state set small. Nuance belongs in
# reasons; propagation needs a tiny deterministic state machine that another agent
# can audit at a glance. Do not turn this into a probabilistic truth oracle.
@dataclass
class Result:
    state: str
    reasons: list[str]
    terminals: set[str]

class ProofError(ValueError):
    pass

def parse_time(value: str) -> datetime:
    v = value[:-1] + "+00:00" if value.endswith("Z") else value
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        raise ProofError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)

def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None

def digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def text(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())

def index(items: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise ProofError(f"{label} must be a list")
    out: dict[str, dict[str, Any]] = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict) or not text(item.get("id")):
            raise ProofError(f"{label}[{i}] needs an object with non-empty id")
        if item["id"] in out:
            raise ProofError(f"duplicate {label} id: {item['id']}")
        out[item["id"]] = item
    return out

def rule(raw: Any) -> tuple[str, list[str], int | None, bool]:
    if not isinstance(raw, dict):
        raise ProofError("rule must be an object")
    kinds = [k for k in ("all", "any", "at_least") if k in raw]
    if len(kinds) != 1:
        raise ProofError("rule needs exactly one of all/any/at_least")
    kind = kinds[0]
    if kind in {"all", "any"}:
        refs = raw[kind]
        if not isinstance(refs, list) or not refs or not all(text(x) for x in refs):
            raise ProofError(f"rule.{kind} must be a non-empty id list")
        return kind, refs, None, False
    cfg = raw["at_least"]
    if not isinstance(cfg, dict):
        raise ProofError("rule.at_least must be an object")
    count, refs = cfg.get("count"), cfg.get("of")
    independent = cfg.get("independent", False)
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ProofError("at_least.count must be a positive integer")
    if not isinstance(refs, list) or not refs or not all(text(x) for x in refs) or count > len(refs):
        raise ProofError("at_least.of/count invalid")
    if not isinstance(independent, bool):
        raise ProofError("at_least.independent must be boolean")
    return kind, refs, count, independent

def bind_local(ev: dict[str, Any], root: Path) -> str | None:
    loc, expected = ev.get("locator"), ev.get("sha256")
    if not isinstance(loc, str) or not loc.startswith("file:"):
        return "sha256 requires file:<path> locator" if expected is not None else None
    rel = loc[5:]
    p = (root / rel).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return f"file locator escapes root: {rel}"
    if not p.is_file():
        return f"bound file missing: {rel}"
    if not isinstance(expected, str) or len(expected) != 64:
        return f"local file evidence requires 64-char sha256: {rel}"
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    return None if actual.lower() == expected.lower() else f"sha256 mismatch: {rel}"

# Footnote for future maintainers: file evidence is root-confined and hash-bound so a
# stable pathname cannot masquerade as stable bytes, and proof metadata cannot read
# arbitrary host files.
def evidence_deadline(ev: dict[str, Any]) -> datetime | None:
    deadlines: list[datetime] = []
    max_age = ev.get("max_age_hours")
    if max_age is not None:
        observed = ev.get("observed_at")
        if not isinstance(max_age, (int, float)) or isinstance(max_age, bool) or max_age <= 0 or not text(observed):
            raise ProofError("invalid freshness metadata")
        deadlines.append(parse_time(observed) + timedelta(hours=float(max_age)))
    if ev.get("valid_until") is not None:
        if not text(ev["valid_until"]):
            raise ProofError("invalid valid_until")
        deadlines.append(parse_time(ev["valid_until"]))
    return min(deadlines) if deadlines else None

def eval_evidence(eid: str, ev: dict[str, Any], now: datetime, context: dict[str, Any], root: Path) -> tuple[Result, datetime | None]:
    status = ev.get("status")
    if not text(status):
        return Result(UNKNOWN, [f"{eid}: missing explicit status"], {eid}), None
    s = status.upper()
    state = VALID if s in PASS else INVALID if s in FAIL else STALE if s in OLD else UNKNOWN if s in UNK else UNKNOWN
    required = ev.get("applies_to", {})
    if not isinstance(required, dict):
        return Result(INVALID, [f"{eid}: applies_to must be object"], {eid}), None
    for k, expected in required.items():
        if context.get(k) != expected:
            return Result(INVALID, [f"{eid}: context mismatch {k}={context.get(k)!r}, expected {expected!r}"], {eid}), None
    binding_error = bind_local(ev, root)
    if binding_error:
        return Result(INVALID, [f"{eid}: {binding_error}"], {eid}), None
    if state != VALID:
        return Result(state, [f"{eid}: explicit status {s}"], {eid}), None
    try:
        deadline = evidence_deadline(ev)
    except ProofError as exc:
        return Result(INVALID, [f"{eid}: {exc}"], {eid}), None
    if deadline is not None and now >= deadline:
        return Result(STALE, [f"{eid}: freshness expired at {deadline.isoformat()}"], {eid}), None
    return Result(VALID, [f"{eid}: evidence valid"], set()), deadline

def distinct_root_state(refs: list[str], results: list[Result], evidence: dict[str, dict[str, Any]], count: int) -> Result:
    roots: dict[str, str] = {}
    for rid in refs:
        if rid not in evidence:
            raise ProofError("at_least.independent may reference direct evidence only")
        root = evidence[rid].get("causal_root")
        if not text(root):
            raise ProofError(f"independent threshold evidence {rid} needs causal_root")
        roots[rid] = root
    by_state: dict[str, set[str]] = {VALID: set(), INVALID: set(), STALE: set(), UNKNOWN: set()}
    reasons_by_state: dict[str, list[str]] = {INVALID: [], STALE: [], UNKNOWN: []}
    terminals_by_state: dict[str, set[str]] = {INVALID: set(), STALE: set(), UNKNOWN: set()}
    for rid, result in zip(refs, results):
        by_state[result.state].add(roots[rid])
        if result.state != VALID:
            reasons_by_state[result.state] += result.reasons
            terminals_by_state[result.state] |= result.terminals
    valid_roots = by_state[VALID]
    if len(valid_roots) >= count:
        return Result(VALID, [f"{len(valid_roots)} independent VALID causal roots >= threshold {count}"], set())
    noninvalid = valid_roots | by_state[STALE] | by_state[UNKNOWN]
    if len(noninvalid) < count:
        active = INVALID
    elif len(valid_roots | by_state[UNKNOWN]) >= count:
        active = UNKNOWN
    else:
        active = STALE
    terminals = terminals_by_state[active]
    reasons = reasons_by_state[active]
    if active == INVALID:
        terminals = terminals_by_state[INVALID] | terminals_by_state[STALE] | terminals_by_state[UNKNOWN]
        reasons = reasons_by_state[INVALID] + reasons_by_state[STALE] + reasons_by_state[UNKNOWN]
    return Result(active, reasons or [f"independent root threshold {count} not met"], terminals)

def combine(kind: str, deps: list[Result], count: int | None, *, independent: bool = False, ref_ids: list[str] | None = None, evidence: dict[str, dict[str, Any]] | None = None) -> Result:
    if independent:
        if kind != "at_least" or count is None or ref_ids is None or evidence is None:
            raise ProofError("independent threshold configuration invalid")
        return distinct_root_state(ref_ids, deps, evidence, count)
    states = [x.state for x in deps]
    if kind == "all":
        if INVALID in states:
            state, active = INVALID, [x for x in deps if x.state == INVALID]
        elif STALE in states:
            state, active = STALE, [x for x in deps if x.state == STALE]
        elif UNKNOWN in states:
            state, active = UNKNOWN, [x for x in deps if x.state == UNKNOWN]
        else:
            return Result(VALID, ["all dependencies VALID"], set())
    elif kind == "any":
        if VALID in states:
            return Result(VALID, ["at least one dependency VALID"], set())
        if all(x == INVALID for x in states):
            state, active = INVALID, deps
        elif UNKNOWN in states:
            state, active = UNKNOWN, [x for x in deps if x.state in {UNKNOWN, STALE}]
        else:
            state, active = STALE, [x for x in deps if x.state == STALE]
    else:
        assert count is not None
        v, u, st = states.count(VALID), states.count(UNKNOWN), states.count(STALE)
        if v >= count:
            return Result(VALID, [f"{v} VALID >= threshold {count}"], set())
        if v + u + st < count:
            state, active = INVALID, [x for x in deps if x.state != VALID]
        elif v + u >= count:
            state, active = UNKNOWN, [x for x in deps if x.state == UNKNOWN]
        else:
            state, active = STALE, [x for x in deps if x.state == STALE]
    terminals, reasons = set(), []
    for x in active:
        terminals |= x.terminals
        reasons += x.reasons
    return Result(state, reasons, terminals)

def minimize_sets(candidates: list[frozenset[str]]) -> list[frozenset[str]]:
    unique = sorted(set(candidates), key=lambda s: (len(s), tuple(sorted(s))))
    minimal: list[frozenset[str]] = []
    for candidate in unique:
        if any(existing <= candidate for existing in minimal):
            continue
        minimal.append(candidate)
        if len(minimal) > MAX_REPAIR_SETS:
            raise ProofError(
                f"repair frontier exceeds {MAX_REPAIR_SETS} minimal alternatives; "
                "simplify the proof contract or decompose the gate instead of emitting a partial frontier"
            )
    return minimal

def combine_repair_sets(groups: list[list[frozenset[str]]]) -> list[frozenset[str]]:
    combos = [frozenset()]
    for options in groups:
        next_combos: list[frozenset[str]] = []
        for left in combos:
            for right in options:
                next_combos.append(left | right)
        combos = minimize_sets(next_combos)
    return combos

def repair_for_rule(kind: str, ref_ids: list[str], dep_results: list[Result], dep_repairs: list[list[frozenset[str]]], count: int | None, *, independent: bool, evidence: dict[str, dict[str, Any]]) -> list[frozenset[str]]:
    if independent:
        assert kind == "at_least" and count is not None
        roots: dict[str, str] = {}
        for rid in ref_ids:
            if rid not in evidence:
                raise ProofError("at_least.independent may reference direct evidence only")
            root = evidence[rid].get("causal_root")
            if not text(root):
                raise ProofError(f"independent threshold evidence {rid} needs causal_root")
            roots[rid] = root
        valid_roots = {roots[rid] for rid, result in zip(ref_ids, dep_results) if result.state == VALID}
        need = count - len(valid_roots)
        if need <= 0:
            return [frozenset()]
        candidates_by_root: dict[str, list[frozenset[str]]] = {}
        for rid, result, repair_sets in zip(ref_ids, dep_results, dep_repairs):
            root = roots[rid]
            if result.state == VALID or root in valid_roots:
                continue
            candidates_by_root.setdefault(root, []).extend(repair_sets)
        if len(candidates_by_root) < need:
            return []
        candidates: list[frozenset[str]] = []
        for chosen_roots in itertools.combinations(sorted(candidates_by_root), need):
            groups = [minimize_sets(candidates_by_root[root]) for root in chosen_roots]
            candidates.extend(combine_repair_sets(groups))
        return minimize_sets(candidates)
    if all(result.state == VALID for result in dep_results):
        return [frozenset()]
    if kind == "all":
        groups = [repair_sets for result, repair_sets in zip(dep_results, dep_repairs) if result.state != VALID]
        return combine_repair_sets(groups)
    if kind == "any":
        candidates = [repair for result, repair_sets in zip(dep_results, dep_repairs) if result.state != VALID for repair in repair_sets]
        return minimize_sets(candidates)
    assert count is not None
    valid_count = sum(result.state == VALID for result in dep_results)
    need = count - valid_count
    if need <= 0:
        return [frozenset()]
    nonvalid = [(i, repair_sets) for i, (result, repair_sets) in enumerate(zip(dep_results, dep_repairs)) if result.state != VALID]
    candidates: list[frozenset[str]] = []
    for chosen in itertools.combinations(nonvalid, need):
        groups = [repair_sets for _, repair_sets in chosen]
        candidates.extend(combine_repair_sets(groups))
    return minimize_sets(candidates)

# Footnote for future maintainers: repair sets are semantic suggestions, not automatic
# repair authority. They identify the smallest primitive evidence sets whose recovery
# would satisfy the present contract; they do not authorize re-running external jobs.
def evaluate(spec: Any, envelope: Any, now: datetime, root: Path) -> dict[str, Any]:
    if not isinstance(spec, dict) or spec.get("schema_version") != 2:
        raise ProofError("proofspec.schema_version must equal 2")
    if not isinstance(envelope, dict) or envelope.get("schema_version") != 2:
        raise ProofError("evidence.schema_version must equal 2")
    # Footnote: evidence producers may not declare mission/claims/gates. The acceptance
    # contract is a separate reviewed surface, blocking self-ratifying runtime payloads.
    forbidden = {"mission", "claims", "gates"} & set(envelope)
    if forbidden:
        raise ProofError(f"evidence envelope contains contract fields: {sorted(forbidden)}")
    mission = spec.get("mission")
    if not isinstance(mission, dict) or not text(mission.get("objective")):
        raise ProofError("mission.objective required")
    context = mission.get("context", {})
    if not isinstance(context, dict):
        raise ProofError("mission.context must be object")
    evidence = index(envelope.get("evidence"), "evidence")
    claims = index(spec.get("claims"), "claims")
    gates = index(spec.get("gates"), "gates")
    known = set(evidence) | set(claims)
    deps: dict[str, list[str]] = {}
    parsed_claim_rules: dict[str, tuple[str, list[str], int | None, bool]] = {}
    parsed_gate_rules: dict[str, tuple[str, list[str], int | None, bool]] = {}
    for cid, c in claims.items():
        parsed = rule(c.get("rule"))
        _, refs, _, independent = parsed
        missing = [x for x in refs if x not in known]
        if missing:
            raise ProofError(f"claim {cid} unknown dependencies: {missing}")
        if independent and any(ref not in evidence for ref in refs):
            raise ProofError(f"claim {cid} independent threshold may reference direct evidence only")
        deps[cid] = refs
        parsed_claim_rules[cid] = parsed
    for gid, g in gates.items():
        parsed = rule(g.get("rule"))
        _, refs, _, independent = parsed
        missing = [x for x in refs if x not in known]
        if missing:
            raise ProofError(f"gate {gid} unknown dependencies: {missing}")
        if independent and any(ref not in evidence for ref in refs):
            raise ProofError(f"gate {gid} independent threshold may reference direct evidence only")
        if g.get("behavior") != "block_unless_valid":
            raise ProofError(f"gate {gid} must use behavior=block_unless_valid")
        parsed_gate_rules[gid] = parsed
    visiting, visited = set(), set()
    def cycle(cid: str) -> None:
        if cid in visited or cid in evidence:
            return
        if cid in visiting:
            raise ProofError(f"cycle detected at {cid}")
        visiting.add(cid)
        for ref_id in deps[cid]:
            if ref_id in claims:
                cycle(ref_id)
        visiting.remove(cid); visited.add(cid)
    for cid in claims:
        cycle(cid)
    er: dict[str, Result] = {}
    deadlines: dict[str, datetime | None] = {}
    repairs: dict[str, list[frozenset[str]]] = {}
    for eid, ev in evidence.items():
        result, deadline = eval_evidence(eid, ev, now, context, root)
        er[eid] = result
        deadlines[eid] = deadline
        repairs[eid] = [frozenset()] if result.state == VALID else [frozenset({eid})]
    cr: dict[str, Result] = {}
    def ref(rid: str) -> Result:
        if rid in er:
            return er[rid]
        if rid in cr:
            return cr[rid]
        kind, refs, count, independent = parsed_claim_rules[rid]
        child_results = [ref(x) for x in refs]
        cr[rid] = combine(kind, child_results, count, independent=independent, ref_ids=refs, evidence=evidence)
        child_repairs = [repairs[x] for x in refs]
        repairs[rid] = repair_for_rule(kind, refs, child_results, child_repairs, count, independent=independent, evidence=evidence)
        return cr[rid]
    for cid in claims:
        ref(cid)
    gr: dict[str, dict[str, Any]] = {}
    for gid, g in gates.items():
        kind, refs, count, independent = parsed_gate_rules[gid]
        child_results = [ref(x) for x in refs]
        r = combine(kind, child_results, count, independent=independent, ref_ids=refs, evidence=evidence)
        repair_sets = repair_for_rule(kind, refs, child_results, [repairs[x] for x in refs], count, independent=independent, evidence=evidence)
        gr[gid] = {
            "state": "OPEN" if r.state == VALID else "CLOSED",
            "proof_state": r.state,
            "action": g.get("action"),
            "terminal_causes": sorted(r.terminals),
            "reasons": r.reasons,
            "minimal_repair_sets": [] if r.state == VALID else [sorted(s) for s in repair_sets],
            "repair_frontier": [] if r.state == VALID else sorted(set().union(*repair_sets) if repair_sets else set()),
            "structural_repair_required": r.state != VALID and not repair_sets,
        }
    reverse: dict[str, set[str]] = {}
    for cid, refs in deps.items():
        for x in refs:
            reverse.setdefault(x, set()).add(f"claim:{cid}")
    for gid, parsed in parsed_gate_rules.items():
        _, refs, _, _ = parsed
        for x in refs:
            reverse.setdefault(x, set()).add(f"gate:{gid}")
    blast: dict[str, dict[str, list[str]]] = {}
    for eid in evidence:
        seen, stack = set(), list(reverse.get(eid, set()))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            raw = node.split(":", 1)[1]
            stack.extend(reverse.get(raw, set()))
        effective = [f"claim:{cid}" for cid, r in cr.items() if r.state != VALID and eid in r.terminals]
        effective += [f"gate:{gid}" for gid, r in gr.items() if r["state"] == "CLOSED" and eid in r["terminal_causes"]]
        blast[eid] = {"structural_descendants": sorted(seen), "effective_current_impact": sorted(effective)}
    used_refs = {ref_id for refs in deps.values() for ref_id in refs}
    for _, refs, _, _ in parsed_gate_rules.values():
        used_refs.update(refs)
    unused_evidence = sorted(set(evidence) - used_refs)
    # Build exact claim→gate reachability so diagnostic-only claims stay visible instead of
    # silently looking operationally enforced.
    gated_claims: set[str] = set()
    for gid, parsed in parsed_gate_rules.items():
        _, refs, _, _ = parsed
        stack = [r for r in refs if r in claims]
        while stack:
            cid = stack.pop()
            if cid in gated_claims:
                continue
            gated_claims.add(cid)
            stack.extend(r for r in deps[cid] if r in claims)
    ungated_claims = sorted(set(claims) - gated_claims)
    relevant_deadlines = [deadline for eid, deadline in deadlines.items() if deadline is not None and any(node.startswith("gate:") for node in blast[eid]["structural_descendants"])]
    next_gate_recheck_at = min(relevant_deadlines) if relevant_deadlines else None
    return {
        "schema_version": 2,
        "engine": "FCMO Proof Spine v0.2",
        "evaluated_at": now.isoformat(),
        "proofspec_digest": digest(spec),
        "evidence_digest": digest(envelope),
        "mission": mission,
        "evidence": {k: {"state": v.state, "reasons": v.reasons, "next_transition_at": iso(deadlines[k]) if v.state == VALID else None, "causal_root": evidence[k].get("causal_root")} for k, v in er.items()},
        "claims": {k: {"state": v.state, "terminal_causes": sorted(v.terminals), "reasons": v.reasons} for k, v in cr.items()},
        "gates": gr,
        "blast_radius": blast,
        "temporal": {"next_gate_recheck_at": iso(next_gate_recheck_at), "strategy": "event-driven plus exact deadline wake-up; no blind polling required"},
        "coverage": {"unused_evidence": unused_evidence, "ungated_claims": ungated_claims},
        "summary": {"open_gates": sorted(k for k, v in gr.items() if v["state"] == "OPEN"), "closed_gates": sorted(k for k, v in gr.items() if v["state"] == "CLOSED")},
        "claim_boundary": "Deterministic propagation, repair-set derivation, temporal wake-up, and counterfactual consequences are proven only under the supplied contract/evidence. External truth, graph completeness, repair authority, and gate authority remain separate claims."
    }

def parse_assumptions(items: list[str]) -> dict[str, str]:
    assumptions: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ProofError("--assume must use EVIDENCE_ID=STATUS")
        eid, status = item.split("=", 1)
        if not text(eid) or not text(status):
            raise ProofError("--assume must use non-empty EVIDENCE_ID=STATUS")
        assumptions[eid] = status
    return assumptions

def apply_assumptions(envelope: dict[str, Any], assumptions: dict[str, str]) -> dict[str, Any]:
    scenario = copy.deepcopy(envelope)
    evidence = index(scenario.get("evidence"), "evidence")
    missing = sorted(set(assumptions) - set(evidence))
    if missing:
        raise ProofError(f"counterfactual unknown evidence ids: {missing}")
    for eid, status in assumptions.items():
        evidence[eid]["status"] = status
    scenario["evidence"] = list(evidence.values())
    return scenario

def state_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    changed_evidence = {key: {"from": before["evidence"][key]["state"], "to": after["evidence"][key]["state"]} for key in before["evidence"] if before["evidence"][key]["state"] != after["evidence"][key]["state"]}
    changed_claims = {key: {"from": before["claims"][key]["state"], "to": after["claims"][key]["state"]} for key in before["claims"] if before["claims"][key]["state"] != after["claims"][key]["state"]}
    changed_gates = {key: {"from": before["gates"][key]["state"], "to": after["gates"][key]["state"]} for key in before["gates"] if before["gates"][key]["state"] != after["gates"][key]["state"]}
    return {"evidence": changed_evidence, "claims": changed_claims, "gates": changed_gates}

# Footnote for future maintainers: counterfactual mode mutates only an in-memory copy
# of the evidence envelope and always exits successfully after a valid simulation.
# A simulation closing a gate is information, not an authorization to change reality.
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("proofspec", type=Path)
    p.add_argument("evidence", type=Path)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--now")
    p.add_argument("--json", action="store_true")
    p.add_argument("--observe-only", action="store_true")
    p.add_argument("--assume", action="append", default=[], metavar="EVIDENCE_ID=STATUS")
    a = p.parse_args()
    try:
        spec = json.loads(a.proofspec.read_text())
        env = json.loads(a.evidence.read_text())
        now = parse_time(a.now) if a.now else datetime.now(timezone.utc)
        baseline = evaluate(spec, env, now, a.root.resolve())
        assumptions = parse_assumptions(a.assume)
        if assumptions:
            scenario_env = apply_assumptions(env, assumptions)
            scenario = evaluate(spec, scenario_env, now, a.root.resolve())
            output = {"mode": "COUNTERFACTUAL", "assumptions": assumptions, "baseline": baseline, "scenario": scenario, "delta": state_delta(baseline, scenario)}
        else:
            output = baseline
    except (OSError, json.JSONDecodeError, ProofError, ValueError) as exc:
        print(f"Proof Spine configuration error: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif assumptions:
        print("COUNTERFACTUAL — no state was mutated")
        for key, change in output["delta"]["claims"].items():
            print(f"CLAIM    {key}: {change['from']} -> {change['to']}")
        for key, change in output["delta"]["gates"].items():
            print(f"GATE     {key}: {change['from']} -> {change['to']}")
    else:
        for k, v in baseline["evidence"].items():
            print(f"EVIDENCE {k}: {v['state']}")
        for k, v in baseline["claims"].items():
            print(f"CLAIM    {k}: {v['state']}")
        for k, v in baseline["gates"].items():
            repairs = v["minimal_repair_sets"]
            repair_text = " | ".join("+".join(x) for x in repairs) if repairs else "-"
            print(f"GATE     {k}: {v['state']} ({v['proof_state']}) causes={','.join(v['terminal_causes']) or '-'} repairs={repair_text}")
        if baseline["temporal"]["next_gate_recheck_at"]:
            print(f"NEXT     gate recheck at {baseline['temporal']['next_gate_recheck_at']}")
    if assumptions:
        return 0
    return 0 if a.observe_only or not baseline["summary"]["closed_gates"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
