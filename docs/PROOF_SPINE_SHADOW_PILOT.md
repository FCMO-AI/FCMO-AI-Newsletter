# Proof Spine shadow pilot — Newsletter evidence adapter

**Date:** 2026-09-14  
**State:** NON_NORMATIVE EXPERIMENT / NO PRODUCTION AUTHORITY

This branch tests one narrow integration boundary: can the Newsletter export enough **public-safe, project-native evidence** for a separate FCMO Proof Spine experiment to evaluate causal validity without copying private doctrine or changing publication behavior?

## Boundary

The Newsletter remains authoritative for its own publication state, health semantics, privacy boundary, localization contract, release gates, and live-site verification.

`tools/proof_spine_shadow_receipt.py` therefore does only three things:

1. executes the same Newsletter-local health commands already used by production health;
2. records their return codes, structured output when available, and a small set of source timestamps already present in public repository data;
3. emits a JSON receipt with an explicit non-authority claim boundary.

It does **not** contain Proof Spine claims, gates, mission rules, publication authority, or action logic.

## Why this is federated instead of vendored

The Proof Spine engine currently lives as a private Agent Hub experiment. Copying it into this public repository would create two independently drifting engines and would expose private institutional implementation merely to run a pilot.

The intended experiment architecture is instead:

```text
Newsletter local checks
        ↓
public-safe shadow receipt
        ↓
Agent Hub experimental proof contract + engine
        ↓
shadow comparison only
```

That keeps local truth production near the project that owns it, while the experimental shared engine reasons over explicit receipts.

## Shadow-only behavior

`.github/workflows/proof-spine-shadow-receipt.yml` is branch-scoped. It uploads the receipt as an artifact and has no deploy, publication, release, issue, notification, or repository-write permission.

A local health check may be unhealthy and the exporter can still complete successfully: the purpose of the workflow is to **observe and preserve evidence**, not to become a hidden replacement gate.

## Success criterion

This pilot is useful only if the external Proof Spine evaluation can compare its decision against the Newsletter's existing local decision surface while preserving important distinctions such as:

- candidate proof vs currently served known-good health;
- `HEALTHY` vs `DEGRADED_ACCEPTABLE` vs `UNHEALTHY` vs `UNKNOWN`;
- scheduled/periodic observations vs exact deterministic freshness deadlines;
- local checker evidence vs shared proof-contract semantics.

Agreement on a healthy sample is specificity evidence, not proof of unique value. Promotion still requires prospective evidence that Proof Spine catches a consequential stale/invalid/unknown dependency state the existing local system would otherwise leave live or materially ambiguous, without unacceptable false blocks.
