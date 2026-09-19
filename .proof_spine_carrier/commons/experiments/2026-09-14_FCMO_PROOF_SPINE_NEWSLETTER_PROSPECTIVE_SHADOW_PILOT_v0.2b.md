# FCMO Proof Spine v0.2b — Newsletter prospective shadow pilot

**Date:** 2026-09-14  
**Authority:** NON_NORMATIVE EXPERIMENT  
**State:** FIRST SOURCE-ALIGNED PROSPECTIVE SAMPLE PRODUCED; private consumer exact-head execution unresolved

## Why this is a material step

The earlier Newsletter evidence was retrospective: it taught Proof Spine that an unproven candidate and a healthy last-known-good live site are different truths.

This pass moved the experiment into **prospective observation**. Before the first branch-only receipt run completed, the experiment had already committed to this falsifiable architecture:

```text
Newsletter-native health checks
        ↓
public-safe evidence-only receipt
        ↓
private Agent Hub Proof Spine contract + engine
        ↓
shadow comparison only
```

The Newsletter producer contains no Proof Spine mission, claim, gate, publication authority, or action semantics. The private Hub consumer owns the experimental causal mapping. This avoids both public→private runtime dependency and two drifting copies of the engine.

## First real receipt: execution proved, applicability later found insufficient

Newsletter draft PR **#43** introduces the branch-only producer on `agent/proof-spine-shadow-pilot`.

Workflow run `34911199573` on head `c57b6e06dcefc24b188df6867fad52851d33145e` completed `success` after actually executing:

- live serving verification;
- live autonomous-surface browser oracle;
- Airlock-backed publication freshness;
- editorial freshness;
- native ES/ZH translation health.

The run uploaded artifact `10374343193`, `newsletter-proof-spine-shadow-receipt`.

Exact identities:

- artifact ZIP SHA-256: `08e1782c1c247e43c3aff881c88dcd4e6b942f8a72415a6193a4eafaacd695a5`;
- extracted receipt JSON SHA-256: `bd0f1595fabca6794c9dc0b9dbd2e33666051fd433e044cbb14417acc62b4a73`;
- receipt bytes: `6004`;
- receipt observation: `2026-09-14T23:59:16.020325Z`.

Every exported local check was `EXECUTED` and `PASS`. The local summary was:

- state: `HEALTHY`;
- quality state: `HEALTHY`.

The decisive editorial metrics were:

- Airlock age ≈ `4.3885 h`;
- newsroom age ≈ `4.3530 h`;
- lead age ≈ `21.1839 h`;
- newest material age ≈ `21.1839 h`;
- lead/newest material: `FCMO-FAD9D0AFD3E4`, importance `9`.

The live surface oracle independently reported publication date `2026-09-14`, Signal Field with `10` current nodes, current Chronology + Research Library, and real-browser verification in Chrome 152.

That receipt remains strong evidence that the public producer actually ran and that those checks passed on its checkout. It is **not grandfathered as proof of current production health** after the source-applicability hardening described below.

## Shadow adapter hardening #1 — localize causes, do not duplicate them

The first Hub consumer draft accidentally included the Airlock deadline inside the `live_editorial_freshness` deadline. That would have recreated the exact anti-pattern v0.2b was designed to eliminate: one Airlock expiry could appear as both Airlock and editorial expiry.

That coupling was removed.

The adapter now treats the branches as:

```text
live_airlock_freshness   ← publication-freshness evidence + Airlock deadline
live_editorial_freshness ← newsroom + Story-supply + lead deadlines
live_serving_probe       ← serving + live-surface oracle
live_translation_health  ← translation-health evidence
```

If the Newsletter's composite editorial checker positively fails at its preliminary `AIRLOCK` stage, Proof Spine maps editorial truth to `UNKNOWN`, not `FAIL`, because the checker did not establish a separate editorial failure after the prerequisite died. Airlock carries the positive failure.

This is important: **failure localization is part of correctness**, not merely diagnostics.

## Shadow adapter hardening #2 — green evidence must still apply to current main

A more serious concurrency problem emerged during this pass: a long-lived experiment branch can fall behind Newsletter `main` while still running its local checks successfully. A green receipt from old Story data, old status data, or old checker semantics must not silently become current production truth.

The public receipt producer now proves applicability separately.

Before and after the observation window it:

1. refreshes `origin/main` through public read-only Git;
2. records the observed `main` SHA;
3. compares the branch checkout with current `main` across material health inputs;
4. rejects silent `main` movement during the observation window.

The material-input set currently covers:

- `newsroom-health.yml`;
- public newsroom status and Story data;
- ES/ZH locale data;
- editorial/translation/live-newsroom checkers;
- the live autonomous-surface browser oracle.

The receipt exports a first-class `source_alignment` state:

- `MATCH` — material inputs match a stable current main;
- `DRIFTED` — material inputs demonstrably differ;
- `CHANGED_DURING_OBSERVATION` — main moved during the observation;
- `UNKNOWN` — applicability could not be established.

Only `MATCH` allows the receipt's local summary to be `HEALTHY` or `UNHEALTHY`. Every other state downgrades the summary to `UNKNOWN`; individual checker outputs remain preserved as observations.

Proof Spine now models that explicitly as:

```text
live_source_alignment
        ↓
live_source_aligned
        ↓
current_live_production_healthy
```

`DRIFTED` is a positive applicability failure for the claim “this receipt represents current main”, **not** positive proof that the public site itself is broken. Fetch uncertainty or moving-main races remain `UNKNOWN`.

This is an Anti-Zombie property: old execution does not become current merely because the artifact survived.

### Consequence for sample #1

Sample #1 predates `source_alignment` and therefore cannot satisfy the hardened contract.

Its original derivation is preserved historically:

- live-health gate → `OPEN / VALID`;
- candidate gate → `CLOSED / UNKNOWN`;
- comparison → `AGREE_HEALTHY`.

Under the hardened current contract, however, the same legacy receipt lacks `live_source_alignment` and is conservatively interpreted as:

- live-health gate → `CLOSED / UNKNOWN`;
- candidate gate → `CLOSED / UNKNOWN`;
- legacy local `HEALTHY` summary versus Proof Spine → `PROOF_SPINE_STRICTER`.

This is not a retroactive claim that the original five checks failed. It is a narrower statement: their applicability to current production was not attested in that receipt. Sample #1 therefore remains producer-execution evidence but is no longer accepted as prospective specificity proof.

The dedicated sample record preserves both the historical and current interpretations rather than silently rewriting the past.

## Preserve local quality nuance without exploding the shared state machine

Newsletter has a legitimate local quality distinction:

- `HEALTHY` while the lead is inside the <=24 h target lane;
- `DEGRADED_ACCEPTABLE` when no eligible <=24 h replacement exists but the lead remains inside the <=48 h acceptable lane;
- `UNHEALTHY` when hard freshness/product conditions fail.

Proof Spine deliberately retains only `VALID / INVALID / STALE / UNKNOWN` as generic epistemic states.

The shadow adapter therefore preserves `DEGRADED_ACCEPTABLE` as **project-local quality metadata beside an OPEN acceptability gate** rather than inventing a fifth generic Proof Spine state. Generic truth composition stays small; domain quality remains expressive.

## First hardened prospective specificity sample — sample #2

The source-aligned producer was pushed at Newsletter head `7d3e8da10425e644696f94131a35eefde167588b`, triggering workflow run `34911725577`.

That run completed **success** and produced artifact `10375010683` after actually executing the full receipt workflow.

Exact artifact identities:

- artifact ZIP SHA-256: `009fba006f619666c77d16e69a8a60966f5f1df729413f48eaa78d91618fa6b6`;
- extracted receipt JSON SHA-256: `527370172cb0badb7a84ff3172bd5f05a2044925cd6c7326a704880084505482`;
- ZIP bytes: `2186`;
- receipt bytes: `7085`;
- receipt observation: `2026-09-15T00:11:03.258046Z`.

Critically, the receipt re-earned current applicability rather than inheriting it:

```text
source_alignment.before = MATCH
main = befabad866e95c1258db1d8edce92ea308291853
material drift = []

source_alignment.after  = MATCH
main = befabad866e95c1258db1d8edce92ea308291853
material drift = []
```

All five project-native checks were again `EXECUTED/PASS`:

- serving health;
- real-browser autonomous-surface oracle;
- Airlock-backed publication freshness;
- editorial freshness;
- native ES/ZH translation health.

The receipt's local result was `HEALTHY / HEALTHY` with:

- Airlock age ≈ `4.5849 h`;
- newsroom age ≈ `4.5494 h`;
- lead/newest material age ≈ `21.3802 h`;
- lead/newest ID `FCMO-FAD9D0AFD3E4`, importance `9`;
- translation grace count `0`, overdue count `0`, missing recent locales `[]`;
- live surface oracle still showing publication date `2026-09-14`, exactly `10` current Signal Field nodes, current Chronology/Research Library, and Chrome 152 browser verification.

This is now the first prospective sample that satisfies the hardened applicability contract.

Under the current v0.2b contract, its **derived** shadow expectation is:

- `live_source_alignment` → `VALID`;
- live-health gate → `OPEN / VALID`;
- candidate gate → `CLOSED / UNKNOWN` because this heartbeat does not attest a candidate transaction;
- comparison → `AGREE_HEALTHY`.

The word **derived** remains important: the public receipt execution is exact and byte-addressed, but the current private Hub consumer itself still lacks exact-head execution evidence in the available runner environment. Do not represent this as an executed private decision receipt yet.

The exact sample is preserved separately as `...PROSPECTIVE_SHADOW_SAMPLE_002_v0.2b.json`.

## Exact deterministic deadlines from the aligned receipt

Sample #2 confirms the same frozen source timestamps and therefore these deterministic boundaries if no event changes the state first:

- next quality transition: `2026-09-15T02:48:13.997039Z` — the lead crosses the strict >24 h target lane and can become `DEGRADED_ACCEPTABLE`;
- Airlock hard deadline: `2026-09-16T01:35:57.409704Z`;
- editorial hard deadline: `2026-09-16T01:38:05.184020Z`.

These preserve Newsletter's existing strict `age > threshold` semantics by placing Proof Spine's inclusive `valid_until` transition one microsecond after the local threshold.

This is not a replacement for event-driven reevaluation. A new Story, new Airlock, new deploy, new `main`, or new health receipt can change the state before any predicted deadline.

## Regression surface after hardening

`tools/test_proof_spine_newsletter_shadow.py` now covers:

1. healthy **aligned** receipt → expected healthy agreement while candidate branch remains UNKNOWN/CLOSED;
2. Airlock failure is not double-counted as an editorial failure;
3. `DEGRADED_ACCEPTABLE` stays domain metadata beside a still-open hard-health gate;
4. missing live check remains UNKNOWN/fail-closed;
5. source drift closes only current-applicability proof and identifies `live_source_alignment` as the terminal cause;
6. a legacy receipt without alignment can no longer prove current health;
7. exact strict-threshold boundary matches Newsletter semantics;
8. editorial deadline remains causally independent of Airlock.

As with the other private Hub additions, these tests are present on the PR branch but **do not yet have exact-head execution evidence** in the current environment. The existing manual exact-head harness now includes this suite.

## What has actually been proven in this pass

The experiment now has direct prospective evidence that:

1. a real FCMO project can produce a public-safe, byte-addressable receipt through its own live checks without giving Proof Spine production authority or copying the shared engine into the project;
2. a stale/unknown checkout is not silently accepted — current source applicability is independently tested;
3. the hardened producer can actually re-earn `MATCH` against a stable current `main` before and after its observation window;
4. a healthy aligned local observation exists as the first legitimate **specificity sample** for the current contract.

The stronger institutional lesson is:

> **evidence validity needs both observation success and applicability to the state it claims to describe.**

The private Hub consumer has not yet executed on an exact checkout of the current PR head, so its shadow decision remains a derivation rather than an executed decision receipt.

## Promotion criterion remains unmet

Sample #2 materially improves the evidence for **specificity**, but does not establish unique-value **sensitivity**.

Proof Spine still must prospectively demonstrate that it catches a consequential stale/invalid/unknown dependency that existing local machinery would otherwise leave live or materially ambiguous, while keeping specificity, maintenance burden, graph completeness risk, and false-block rate acceptable.

The pilot therefore remains shadow-only. Do not inject an artificial production failure merely to manufacture a win; allow real project events, source drift, or freshness boundaries to produce discriminating samples and preserve their receipts exactly.
