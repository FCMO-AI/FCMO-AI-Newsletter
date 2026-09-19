# FCMO Proof Spine v0.2 — Dependency-Aware Belief Invalidation

**Date:** 2026-09-14  
**Authority:** NON_NORMATIVE EXPERIMENT  
**State:** ACTIVE CANDIDATE; not a required Hub gate  
**Supersedes:** v0.1 as the primary research direction, without deleting v0.1 evidence/history

## Thesis

FCMO already knows that material claims should remain attached to evidence. The missing capability is **transitive invalidation**: when a premise becomes invalid, stale, unknown, out-of-regime, or byte-mismatched, FCMO should be able to deterministically recompute every dependent conclusion and close any action gate whose proof is no longer live.

The target capability is:

`EVIDENCE -> DERIVED CLAIMS -> DECISION/GATE`

with automatic reverse consequences:

`PREMISE DIES -> DEPENDENT CLAIMS LOSE VALIDITY -> GATE CLOSES -> ROOT CAUSE / REPAIR PATH IS TRACEABLE`

This is not a truth oracle. It is a deterministic dependency engine over an explicit proof contract.

## The key architectural bonk: contract != evidence

Proof Spine v0.2 separates two surfaces:

1. **Proof contract (`proofspec`)** — versioned mission, dependency graph, combination rules, and fail-closed gates. This should be reviewed like code/configuration.
2. **Evidence envelope** — runtime observations, receipts, test results, freshness timestamps, context/regime metadata, causal-root metadata, and optional byte bindings.

The evidence producer is forbidden from declaring `mission`, `claims`, or `gates`. A producer therefore cannot make itself pass by silently changing the acceptance rule in the same runtime payload.

Both payloads receive independent deterministic SHA-256 digests in the report so a consumer can bind a decision to the exact contract and exact evidence evaluated.

## Four states only

Primitive evidence and derived claims resolve to:

- `VALID` — currently sufficient under the contract;
- `INVALID` — positively failed, mismatched, or unusable;
- `STALE` — previously/currently plausible evidence has exceeded its allowed temporal window;
- `UNKNOWN` — present truth is not established.

Keep the state machine small. Nuance belongs in reason metadata, not dozens of statuses with ambiguous propagation.

## Deterministic composition

A claim contains exactly one rule:

- `all`: every dependency must be `VALID`;
- `any`: one `VALID` dependency is sufficient;
- `at_least`: N of M dependencies must be `VALID`.

`at_least` can additionally request `independent: true`. In that mode, every referenced item must be **direct evidence** with a declared `causal_root`, and the threshold counts unique causal roots rather than file/result count. Two mirrors of one report no longer masquerade as two confirmations.

This matters because invalidation must not be naive. If an old source goes stale but an independent live source still satisfies an `any` rule, the downstream claim remains valid. Conversely, cosmetic redundancy must not create fake resilience.

Cycles and references to nonexistent dependencies are configuration errors and fail before evaluation.

## Evidence validity

v0.2 currently supports these deterministic invalidators:

- explicit PASS/FAIL/UNKNOWN/STALE-like status;
- `observed_at + max_age_hours` freshness expiry;
- explicit `valid_until` expiry;
- exact mission-context applicability through `applies_to` key/value matching;
- local `file:` evidence root confinement and SHA-256 byte binding.

External truth remains external. Declaring `status: PASS` does not cryptographically prove that an external benchmark happened; adapters/receipts must earn that evidence separately.

## Gates

A gate is intentionally simple:

`behavior = block_unless_valid`

A gate opens only when its rule resolves `VALID`. `INVALID`, `STALE`, and `UNKNOWN` all close it. The CLI therefore exits non-zero when any enforcement gate is closed unless explicitly run in observation-only mode.

The engine **does not execute the action**. It emits the gate state. The consuming repository decides whether a closed gate blocks publish/deploy/promote/advance-current/accept-benchmark/etc. This preserves project authority boundaries.

## Blast radius

For every evidence item, v0.2 reports:

- **structural descendants** — every claim/gate that depends on it, directly or transitively;
- **effective current impact** — currently non-valid downstream claims/gates for which that evidence is an active terminal cause.

This gives FCMO a machine answer to: “If this premise dies, what else should I stop believing?”

## Repair frontier — minimum work to reopen a gate

A closed gate now returns **minimal repair sets**, not merely every broken thing it can see.

Examples:

- `all(A,B)` with both broken -> repair set `{A,B}`;
- `any(A,B)` with both broken -> alternative repair sets `{A}` **or** `{B}`;
- `at_least(2 of A,B,C)` -> only enough broken branches to restore the threshold are proposed;
- independent quorums preserve causal-root requirements while calculating repair choices.

The union is exposed as `repair_frontier` for discovery, while `minimal_repair_sets` preserves the alternatives. If the current evidence set cannot satisfy an independent-root requirement, the gate reports `structural_repair_required=true` instead of pretending that revalidating existing evidence is enough. If more than 64 minimal alternatives would be required, evaluation fails explicitly rather than silently truncating the frontier. These are diagnostic suggestions only: they do **not** grant authority to rerun jobs, contact systems, publish, or mutate production.

## Temporal wake-up — stop dumb polling

For valid time-bounded evidence the engine computes the exact `next_transition_at`. It then emits the earliest `next_gate_recheck_at` among evidence that is structurally upstream of an action gate.

This enables a cheap hybrid runtime:

`EVENT ARRIVES -> EVALUATE NOW`

or

`NEXT EXPIRY DEADLINE ARRIVES -> EVALUATE NOW`

Unrelated timed evidence does not force a gate wake-up. Exact expiry is fail-closed: at the expiry instant, the evidence is `STALE`.

## Counterfactual mode — ask “what would break?” without breaking it

The CLI now accepts repeatable `--assume EVIDENCE_ID=STATUS` overrides. The override is applied only to an in-memory copy, and the engine reports claim/gate deltas between baseline and scenario.

Example conceptual query:

`--assume arb_public_safe=STALE`

can report:

`production_current: VALID -> STALE`

`advance_current_edition: OPEN -> CLOSED`

Counterfactual mode always remains observational; a simulated closed gate is information, not an external action or permission.

## Coverage lint — expose silent graph omissions

Proof Spine cannot prove that the dependency graph is complete. It can, however, make obvious omissions harder to miss. The report now exposes:

- evidence declared but unused anywhere in the proof graph;
- claims that have no path to any enforcement gate.

These are not automatically errors because diagnostic-only claims/evidence can be legitimate. They are audit surfaces for the human/agent designing the contract.

## Concrete Newsletter experiment

The canonical Newsletter product goal already defines a causal chain from fresh public-safe ARB evidence through release gates and live browser verification to reader-visible production health.

The included example models:

`arb_public_safe`
→ `upstream_fresh`
→ `release_candidate_valid`
→ `live_verified`
→ `today_edition_publishable`
→ `production_current`
→ gate `advance_current_edition`

With identical contract and evidence bytes:

- while ARB evidence remains inside its freshness window: every claim is `VALID`; gate is `OPEN`; process exits 0;
- at/after its exact 24h expiry: `arb_public_safe` becomes `STALE`; every dependent claim becomes `STALE`; gate is `CLOSED`; terminal cause and minimal repair set are both `arb_public_safe`; process exits 1.

The browser receipt may still be PASS. The system correctly concludes that “the page renders” is no longer enough to prove “the newspaper is current.”

The fresh run also emits the exact next gate recheck deadline, so a production adapter need not poll continuously.

## Adversarial coverage after the current BONK

`tools/test_proof_spine_v2.py` now exercises **24 cases** covering:

1. fresh evidence opens a gate;
2. stale evidence cascades transitively and closes it;
3. exact expiry is stale rather than receiving a hidden grace instant;
4. unrelated stale evidence has no effect and is surfaced as unused;
5. a valid `any` alternative masks a stale branch;
6. ordinary `at_least` thresholds work;
7. independent thresholds reject duplicate causal roots;
8. independent thresholds accept genuinely distinct roots;
9. independent thresholds require explicit causal-root metadata;
10. cycles are rejected;
11. unknown references are rejected;
12. runtime evidence cannot rewrite the proof contract;
13. context/regime mismatch invalidates evidence;
14. UNKNOWN fails closed;
15. byte hash mismatch invalidates local evidence;
16. contract and evidence have independent digests;
17. next gate recheck equals the exact evidence expiry;
18. a simple stale chain yields one minimal terminal repair;
19. `any` produces alternative minimal repair paths;
20. `all` requires all blocking terminal repairs;
21. counterfactual evaluation mutates only a copy and reports gate/claim deltas;
22. counterfactual references to nonexistent evidence are rejected;
23. repair-frontier overflow fails explicitly instead of emitting a misleading partial answer;
24. ungated claims are visible in coverage lint.

Local candidate execution after this BONK: **24/24 PASS**. The deterministic Newsletter fresh/stale/counterfactual scenarios also behaved as specified. This is still not a claim that the exact GitHub PR snapshot passed the full Hub integrity runner.

## Promotion/disproof conditions

Do **not** promote v0.2 merely because its tests are green.

Promote toward shared infrastructure only if prospective use in at least one real FCMO system demonstrates that it catches or prevents a consequential stale/invalid dependency state that existing local mechanisms would otherwise leave live, without creating unacceptable false blocks or maintenance burden.

Kill or redesign the direction if:

- maintaining proof contracts costs more than the failures they prevent;
- important dependencies cannot be represented without an unsafe mini-language;
- false invalidation becomes common;
- agents simply route around closed gates;
- project-local mechanisms solve the same problem more cleanly;
- dependency-model incompleteness creates more confidence than safety;
- repair-set combinatorics or proof-graph size become operationally expensive enough that a simpler mechanism dominates.

## Claim boundary

Proof Spine can deterministically prove **what follows from the declared graph and evidence states**. It cannot independently prove that the graph contains every real-world dependency, that external evidence is truthful, that a proposed repair is authorized, that a gate has legitimate authority, or that the chosen mission is correct. Those remain separate evidence/authority/design problems.
