# Proof Spine shadow pilot — Newsletter evidence adapter

**Date:** 2026-09-14  
**State:** NON_NORMATIVE EXPERIMENT / NO PRODUCTION AUTHORITY

This branch tests one narrow integration boundary: can the Newsletter export enough **public-safe, project-native evidence** for a separate FCMO Proof Spine experiment to evaluate causal validity without copying private doctrine or changing publication behavior?

## Boundary

The Newsletter remains authoritative for its own publication state, health semantics, privacy boundary, localization contract, release gates, and live-site verification.

`tools/proof_spine_shadow_receipt.py` therefore does four bounded things:

1. executes the same Newsletter-local health commands already used by production health;
2. records their return codes, structured output when available, and a small set of source timestamps already present in public repository data;
3. proves whether the checkout's **material health inputs** still match one stable current `origin/main` before and after the observation window;
4. emits a JSON receipt with an explicit non-authority claim boundary.

It does **not** contain Proof Spine claims, gates, mission rules, publication authority, or action logic.

## Why source alignment is part of evidence

A branch can execute every local health check successfully while its Story data, status data, locale data, or checker semantics have drifted from current `main`. In that case, a green result is real execution evidence but not adequate evidence for the stronger claim “this describes current production.”

The receipt therefore exposes `source_alignment` separately from health:

- `MATCH` — all declared material health inputs match the same stable current-main SHA before and after the observation;
- `DRIFTED` — at least one material input differs;
- `CHANGED_DURING_OBSERVATION` — `main` changed during the observation window;
- `UNKNOWN` — current applicability could not be established.

Only `MATCH` allows the receipt summary to become `HEALTHY` or `UNHEALTHY`. Any other alignment state yields summary `UNKNOWN` while preserving the individual checker outputs as observations.

**Footnote for future maintainers:** `DRIFTED` does not mean the live website is broken. It means this checkout cannot truthfully certify the current-main health claim. Keep applicability failure separate from product failure.

Material alignment currently covers:

- `.github/workflows/newsroom-health.yml`;
- `site/data/newsroom-status.json`;
- `site/data/stories.json`;
- native `es-419` and `zh-Hans` data;
- editorial, translation, and live-newsroom verification tools;
- the real-browser autonomous-surface oracle.

## Why this is federated instead of vendored

The Proof Spine engine currently lives as a private Agent Hub experiment. Copying it into this public repository would create two independently drifting engines and would expose private institutional implementation merely to run a pilot.

The intended experiment architecture is instead:

```text
Newsletter local checks + source applicability
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

A local health check may be unhealthy, source applicability may be unknown, or the branch may be drifted and the exporter can still complete successfully: the purpose of the workflow is to **observe and preserve evidence**, not to become a hidden replacement gate.

## Prospective evidence already obtained

The first producer run proved that the adapter and all five local checks could execute prospectively, but its receipt predated source-alignment attestation and is therefore not grandfathered as current-health proof.

The hardened second run, `34911725577`, on branch head `7d3e8da10425e644696f94131a35eefde167588b`, produced an aligned receipt with:

- `source_alignment.before = MATCH`;
- `source_alignment.after = MATCH`;
- the same observed current-main SHA `befabad866e95c1258db1d8edce92ea308291853` at both boundaries;
- no drifted material paths;
- all five project-native health checks `EXECUTED/PASS`;
- local state/quality `HEALTHY / HEALTHY`.

That is specificity evidence for the **public evidence boundary**. It does not prove the private Agent Hub consumer, grant publication authority, or establish unique Proof Spine value.

## Success criterion

This pilot is useful only if the external Proof Spine evaluation can compare its decision against the Newsletter's existing local decision surface while preserving important distinctions such as:

- candidate proof vs currently served known-good health;
- evidence execution vs applicability to current `main`;
- `HEALTHY` vs `DEGRADED_ACCEPTABLE` vs `UNHEALTHY` vs `UNKNOWN`;
- scheduled/periodic observations vs exact deterministic freshness deadlines;
- local checker evidence vs shared proof-contract semantics.

Agreement on an aligned healthy sample is specificity evidence, not proof of unique value. Promotion still requires prospective evidence that Proof Spine catches a consequential stale/invalid/unknown dependency state the existing local system would otherwise leave live or materially ambiguous, without unacceptable false blocks or maintenance burden.
