# FCMO Proof Spine v0.1 — Claim→Evidence Integrity Experiment

**Date:** 2026-09-14  
**Authority:** NON_NORMATIVE EXPERIMENT  
**Status:** READY FOR REVIEW / NOT CANON  
**Scope:** cross-project proof hygiene; no change to Core, Worthy Work, Governance, policy, identity, or promotion authority

## 1. Why this exists

FCMO already has strong rules about truth, evidence, authority, freshness, exact-snapshot validation, and proving promised outcomes. The Hub also has an integrity receipt for the repository itself.

A remaining operational gap sits *inside individual missions*: a report can contain several different kinds of claims — “this ran,” “this is faster,” “this is complete,” “this evidence is current,” “we are authorized to do this” — while the supporting evidence is scattered across commands, artifacts, benchmarks, approvals, source material, and receipts. Humans and agents can read that structure, but today there is no small portable mechanism that rejects the most common evidence-category errors before they become status language.

Proof Spine experiments with such a mechanism.

> **A material claim should be mechanically traceable to evidence whose class can actually support that class of claim.**

Proof Spine is deliberately narrower than a truth oracle. It validates the *shape and binding of proof*, not reality itself.

## 2. Hypothesis

If material mission claims are represented as a compact claim→evidence graph and checked by a portable validator, FCMO can reduce false completion, stale-current claims, benchmark theater, accidental authority laundering, and “attempted therefore executed” status errors without requiring heavyweight process or vendor-specific infrastructure.

## 3. Baseline

Without Proof Spine, mission proof is usually prose plus whatever execution artifacts the acting agent chooses to surface. That can be excellent, but category mistakes remain review-dependent:

- a queued/attempted job can be described as executed;
- an artifact can be mistaken for proof that it was tested;
- an old observation can be described as current;
- a benchmark can omit its comparison and still sound like a performance result;
- a technical artifact can be mistaken for authority to promote or deploy;
- a broad “done” statement can outrun its actual acceptance condition.

The existing Hub integrity receipt correctly proves repository-level checks for an exact snapshot; it does not attempt to model all claims made by arbitrary FCMO missions, and Proof Spine does not replace it.

## 4. Intervention

`tools/proof_spine.py` validates a JSON receipt containing:

- one explicit mission objective;
- typed claims: `fact`, `execution`, `performance`, `completion`, `freshness`, `authority`, or `decision`;
- typed evidence: source/artifact/observation, execution/test/benchmark/receipt, approval/policy/user instruction, or explicitly weak `plan`/`attempt` records;
- claim materiality and an explicit boundary for material/critical claims;
- freshness windows via `observed_at` + `max_age_hours`;
- optional local `file:` evidence binding via SHA-256;
- explicit acceptance criteria for completion claims;
- explicit comparisons for performance claims.

The validator returns non-zero on unsupported or mismatched claims. Warnings can be promoted to failures with `--strict`.

### Example invocation

```bash
python tools/proof_spine.py mission-proof.json --root . --strict
```

Machine-readable output:

```bash
python tools/proof_spine.py mission-proof.json --root . --json
```

Deterministic freshness testing:

```bash
python tools/proof_spine.py mission-proof.json --now 2026-09-14T20:00:00Z
```

## 5. Adversarial properties in v0.1

The companion test suite deliberately verifies that:

1. an `attempt` cannot prove an execution claim;
2. an unknown evidence reference fails;
3. stale evidence cannot prove freshness;
4. an artifact cannot prove authority;
5. a changed local artifact fails its recorded SHA-256 binding;
6. material/critical claims require an explicit boundary;
7. a performance claim needs a passing benchmark/test *and* a declared comparison;
8. a fully supported mixed receipt passes.

These are not merely schema tests. They target category errors that produce confident but false status language.

## 6. Claim boundary

A `PASS` means:

> the declared claims satisfy Proof Spine's traceability, evidence-class, freshness, and optional local byte-binding rules.

A `PASS` does **not** mean:

- an external source is true;
- a benchmark methodology is scientifically good;
- an approval is legitimate beyond the cited authority surface;
- a command actually ran merely because JSON says it did;
- a mission is objectively valuable;
- promotion/release authority exists;
- Core, policy, Worthy Work, Governance, or repository-local law can be skipped.

For exact execution evidence, Proof Spine should ideally cite a real external/portable receipt that can be independently verified. It must never turn self-reported metadata into stronger evidence than it is.

## 7. Disproof / retirement conditions

Do **not** promote this experiment merely because the code works.

Retire or substantially redesign it if field use shows that any of the following dominate:

- agents spend more effort authoring receipts than the review risk justifies;
- the fixed claim/evidence taxonomy causes agents to distort real missions to fit the schema;
- teams begin treating `PASS` as truth or authority despite the explicit boundary;
- the validator catches few meaningful errors beyond what existing proof practice already catches;
- attackers can routinely launder unsupported claims through allowed evidence classes without being obvious to reviewers;
- repository/project-local proof mechanisms solve the same problem more causally with lower carrying cost.

## 8. Success evidence required before any wider adoption

A useful next experiment would apply Proof Spine prospectively to several materially different FCMO tasks, preferably including:

- a software release or integration;
- a benchmark/performance claim;
- a research/current-state claim with real freshness decay;
- an authority-sensitive publish/merge/deploy decision.

Record whether it catches a real proof defect, changes a status claim, adds review burden, or merely restates what competent reviewers already knew.

Promotion should require evidence that the mechanism improves decision quality or review reliability in real work, not aesthetic enthusiasm for the schema.

## 9. Why this is FCMO-shaped

Proof Spine is intentionally small. It does not create a new doctrine layer. It gives existing FCMO principles a portable executable edge:

**mission → claim → evidence class → exact boundary → current binding → truthful status**

That is the whole bet.
