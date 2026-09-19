# FCMO Proof Spine — Newsletter pre-action shadow field observation v0.2e

**Date:** 2026-09-16  
**Authority:** NON_NORMATIVE EXPERIMENT  
**State:** UNATTENDED PRE-ACTION OBSERVER EXECUTED; NATURAL CATCH-BEFORE-LATER-ACTION CRITERION STILL OPEN

## Purpose

Test the next discriminator after the retrospective Newsletter localization divergence: can the project emit an unattended, evidence-only observation of a concrete candidate's release prerequisite **before any future consequential action**, while preserving the separation between candidate validity and current live-production health?

The experiment remains shadow-only. Newsletter owns publication/release semantics and production authority; Proof Spine owns only the experimental causal composition of supplied evidence.

## Natural recurrence on current Newsletter main

Current Newsletter `main` at observation time:

`1af947d3be9f76ea963b4b293953dedb6729bb83`

The same localization failure class recurred naturally:

1. Pages run `35138995503` on that SHA completed `success` after starting at `2026-09-16T19:10:59Z`;
2. immediately triggered production-health run `35139216281` completed `failure` after starting at `2026-09-16T19:13:09Z`;
3. the failing branch was native-edition translation health while serving, browser-surface, publication-freshness and editorial-freshness observations remained positive;
4. Newsletter `main` remained unchanged through the later shadow observation.

This recurrence confirms the previously diagnosed release-edge gap remained live in production while the project-local repair PR stayed draft/unmerged.

## New project-local evidence producer

Newsletter branch:

`agent/proof-spine-preaction-shadow-v0.2e`

Draft PR:

`FCMO-AI/FCMO-AI-Newsletter#45`

The branch adds an evidence-only adapter around project-owned truth surfaces:

- `tools/proof_spine_shadow_receipt.py` — existing live-health/source-alignment observation boundary;
- `tools/proof_spine_preaction_shadow_receipt.py` — candidate native-edition observation;
- `tests/test_proof_spine_preaction_shadow.py` — producer regressions;
- `.github/workflows/proof-spine-preaction-shadow.yml` — read-only execution + artifact publication.

The producer contains no Proof Spine mission, claims, gates or deployment authority.

## Executed hosted evidence

Workflow run `35140061610`, job `104942058126`, completed `success` and executed every declared step.

Producer regression result:

- **4/4 PASS**.

Exact observation:

- observed at `2026-09-16T19:22:02.358706Z`;
- `source_alignment = MATCH` before and after;
- represented current main = `1af947d3be9f76ea963b4b293953dedb6729bb83`;
- canonical Story identities = `43`;
- native-complete Story identities = `42`;
- pending native-edition count = `1`;
- pending identity = `FCMO-7EBD0FA07C12`;
- candidate native-edition state = `INCOMPLETE_NATIVE_EDITIONS`;
- live local health = `UNHEALTHY / UNHEALTHY`;
- live `serving_health`, `surface_oracle`, `publication_freshness`, `editorial_freshness` = `PASS`;
- live `translation_health = FAIL`;
- upstream ARB-publication synchronization was intentionally `NOT_OBSERVED / UNKNOWN` in this minimal pre-action run.

Artifact `10464627216` exact identities, recomputed from downloaded bytes:

- ZIP bytes = `3112`;
- ZIP SHA-256 = `ff802fb3816c1c41ddd5ad897aa0c0b35d1180714b3bce5cf3215d2843d2507c`;
- inner JSON bytes = `10157`;
- inner JSON SHA-256 = `61bd07a09ff31b648f566fcc6323daa193b1901394e2d1b2f12f23762be260d4`.

The earlier working note that listed a different inner JSON size/hash was wrong and is superseded by these recomputed byte identities.

## Consumer-side causal mapping

`tools/proof_spine_newsletter_shadow.py` now accepts the v2 pre-action receipt and maps the candidate localization observation under a strict applicability guard:

- `COMPLETE_NATIVE_EDITIONS + source_alignment=MATCH -> PASS`;
- `INCOMPLETE_NATIVE_EDITIONS + source_alignment=MATCH -> FAIL`;
- source drift/change/unknown applicability -> `UNKNOWN` regardless of local positive/negative candidate observation;
- legacy v1 receipts -> `UNKNOWN` for candidate localization rather than retroactive proof.

The producer still cannot author either proof law or release authority.

The predeploy contract remains:

`commons/experiments/2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_PROOFSPEC_v0.2c.json`

with primitive `candidate_localization_ready` and gate `candidate_may_enter_deploy`.

New consumer regression surface:

`tools/test_proof_spine_newsletter_preaction.py`

covers legacy unknown, aligned incomplete failure, drift downgrade to unknown, complete-localization non-self-ratification, and the field fixture.

## Independent semantic replay of the exact artifact

Because the private Agent Hub hosted runner still fails before checkout, the exact branch consumer has **not** yet executed under hosted exact-head CI.

An independent side-effect-free semantic replay over the exact downloaded artifact verifies the decisive composition implied by the reviewed contracts:

```text
candidate_arb_public_safe      UNKNOWN
candidate_six_release_gates   UNKNOWN
publication_authority         UNKNOWN
candidate_localization_ready  FAIL
                              ↓
candidate_may_enter_deploy    INVALID / CLOSED
```

The live branch is independently:

```text
live_source_alignment         PASS
live_serving_probe            PASS
live_airlock_freshness        PASS
live_editorial_freshness      PASS
live_translation_health       FAIL
                              ↓
represent_live_production_healthy = INVALID / CLOSED
```

### Counterfactual causal-isolation check

A deep-copy counterfactual changed **only** the live translation-health premise from `FAIL` to `PASS`, leaving the candidate localization observation untouched.

Result:

```text
represent_live_production_healthy = VALID / OPEN
candidate_may_enter_deploy         = INVALID / CLOSED
```

This independently confirms the intended ontology: an invalid candidate does not poison a valid current-live branch, and a live-health repair does not launder an invalid candidate.

This replay is not represented as execution of the exact Hub Python blobs. It is corroborating semantic evidence while the Hub runner remains unavailable.

## Chronology boundary — not prevention evidence yet

The pre-action receipt was produced at `19:22:02Z`, **after** the current-main Pages deployment at `19:10:59Z` and its failing health follow-up.

A subsequent exact-SHA Actions query found only those two production runs for `1af947d3...`; Newsletter `main` also remained on the same SHA. There was therefore **no later deployment after the shadow observation** against which to claim a natural catch-before-action event.

Correct claim:

> An unattended read-only pre-action observer now exists and executed successfully against the current candidate, detecting the exact unresolved localization prerequisite with current-main applicability.

Not yet supported:

- that Proof Spine prevented a deployment;
- that the shadow caught a later real deployment before it happened;
- that the project should delegate release authority to Proof Spine;
- that the universal experiment is ready for promotion.

## Private Hub exact-head substrate boundary

A fourth discriminating hosted attempt was made only to test whether the private Hub runner substrate had recovered:

- run `35140824629`;
- job `104944617485`;
- conclusion `failure`;
- `steps = null` again.

No checkout or test step began. The automatic branch trigger was removed immediately afterward.

The four independent observations are now:

- `34904535360` — `steps = null`;
- `35033314130`, job `104596603493` — `steps = null`;
- `35044247338`, job `104630537501` — `steps = null`;
- `35140824629`, job `104944617485` — `steps = null`.

This remains an **UNEXECUTED substrate state**, not a Proof Spine test failure.

## Field result

This BONK materially advances the experiment from retrospective reconstruction to an **executed unattended pre-action observation boundary** on current production source state.

It does **not** yet cross the stronger natural sensitivity threshold because no consequential action occurred after the observation while the invalid state remained present.

The next discriminating evidence should come from normal project operation, not injected failure:

1. the observer runs before a naturally attempted candidate advancement;
2. the contract independently yields `CLOSED / INVALID|STALE|UNKNOWN` for a real prerequisite;
3. existing local machinery would otherwise have allowed or materially ambiguated the action;
4. unrelated last-known-good/live truths remain correctly isolated;
5. false-block and maintenance burden remain acceptable across repeated healthy cycles.

Until then the experiment remains shadow-only and non-normative.