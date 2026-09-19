# FCMO Proof Spine — Newsletter Field Correction v0.2b

**Date:** 2026-09-14  
**Authority:** NON_NORMATIVE EXPERIMENT  
**State:** ACTIVE FIELD CORRECTION  
**Applies to:** the Newsletter example inside Proof Spine v0.2; this does not supersede the generic v0.2 engine

## Why this correction exists

The original Newsletter proofspec in the v0.2 experiment modeled one mostly linear chain:

`candidate evidence -> release -> deploy/browser -> production current`

That was useful for demonstrating transitive freshness invalidation, but a real Newsletter workflow case exposed a material modeling error: **candidate advancement truth and currently served last-known-good production health are not the same causal object.**

Newsletter's canonical product goal is explicitly fail-closed. If a new candidate cannot advance, the previous known-good edition is meant to remain live. Therefore:

> **A failed, skipped, stale, or unknown candidate must close the candidate-advancement gate without automatically declaring the already served known-good production release unhealthy.**

This is not a cosmetic graph refactor. It changes what Proof Spine is allowed to conclude.

## Field observation that forced the change

Repository: `FCMO-AI/FCMO-AI-Newsletter`

On SHA `29ab040bcfe2457735e72033670c61953221423b`:

- Pages deploy run `34799517755` / run #118 concluded **`skipped`** at `2026-09-14T02:31:52Z`.
- The workflow-run-triggered production health run `34799521505` / run #125 followed at `2026-09-14T02:31:56Z` and also concluded **`skipped`**.
- Its then-present jobs — `editorial-freshness`, `publication-freshness`, and `serving-health` — were all skipped and executed no steps.

The local workflow explains why: its jobs run on `workflow_run` only when the triggering Pages workflow concluded `success`.

This establishes **absence of candidate health proof**, not positive proof that the currently served site was unhealthy.

Later the same day, independent production-health run `34901292822` / run #147 on SHA `b17e5e63d69713e3538016ae91707ad18e477240` concluded **`success`**, with `editorial-freshness`, `publication-freshness`, `serving-health`, and `translation-health` all successful. Because this later run is on a different SHA and at a later time, it is evidence that live health is independently measurable — **not** proof of the site's exact state at 02:31Z.

The exact receipts are preserved in `2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_FIELD_OBSERVATION_v0.2b.json`.

## Correct causal model

v0.2b splits the Newsletter model into two proof trees.

### Tree A — candidate advancement

`candidate_arb_public_safe`
→ `candidate_upstream_fresh`
→ `candidate_ready_to_deploy`
→ `candidate_deployed`
→ `candidate_live_verified`
→ `candidate_can_advance`
→ gate `advance_candidate_current_edition`

A skipped deploy is represented as **`UNKNOWN`**, because no positive deployment truth was established. `UNKNOWN` correctly closes the fail-closed advancement gate.

### Tree B — currently served known-good production

`live_serving_probe`
+ `live_airlock_freshness`
+ `live_editorial_freshness`
+ `live_translation_health`
→ `current_live_production_healthy`
→ gate `represent_live_production_healthy`

This tree requires its own evidence. Candidate failure is not one of its dependencies.

## Important semantic rule discovered by the field case

> **Operational proximity is not causal dependency.**

A candidate deployment and the live site are operationally related. That does not mean every candidate failure invalidates every claim about the live site.

The same rule generalizes beyond Newsletter:

- a failed new BLM checkpoint does not invalidate the last validated checkpoint;
- a bad future .CMPCT candidate does not erase the validity of the currently released version;
- a failed Hermes upgrade does not imply the currently deployed Hermes instance is broken;
- an expired benchmark for a proposed change does not retroactively falsify an independently proven production baseline.

Proof Spine should propagate invalidity only across **declared real prerequisites**, not across vague system adjacency.

## Why `SKIPPED -> UNKNOWN`, not `INVALID`

A skipped check establishes that the check did not produce the positive proof the gate requires. It normally does **not** establish that the underlying proposition is false.

Therefore the conservative mapping is:

`SKIPPED -> UNKNOWN -> fail-closed gate CLOSED`

This preserves epistemic truth while still preventing unsafe advancement.

Project adapters may use stronger mappings when local semantics justify them, but a generic adapter must not silently translate non-execution into positive failure.

## v0.2b regression proof

`tools/test_proof_spine_newsletter_v02b.py` adds three branch-isolation regressions:

1. a skipped/unknown candidate closes only `advance_candidate_current_edition` while independently valid live evidence keeps `represent_live_production_healthy` open;
2. a live serving failure closes only the live-health gate and does not retroactively erase an otherwise valid candidate proof chain;
3. exact candidate freshness expiry closes the candidate branch while independent live known-good health remains valid.

The tests deliberately use the unchanged generic v0.2 engine. This correction therefore tests **better contract modeling**, not a special-case engine hack.

## Negative knowledge preserved

The original linear Newsletter v0.2 proofspec remains in the branch as historical experiment evidence. It should no longer be treated as the preferred Newsletter model.

Its useful result survives: stale upstream evidence can transitively revoke a downstream current-edition claim even while a browser receipt remains green.

Its rejected overreach is now explicit: **candidate proof and live known-good health must not be collapsed into one chain merely because both concern the same product.**

## Promotion consequence

This correction makes Proof Spine harder to promote, not easier.

A prospective field pilot must now demonstrate both:

- **sensitivity:** it closes a consequential gate when a real prerequisite becomes stale/invalid/unknown and existing local machinery would otherwise leave the state ambiguous or live;
- **specificity:** it does **not** close unrelated gates or manufacture incidents through over-broad graph coupling.

A system that catches stale truth but causes false production-health incidents is not an improvement.

## Next field threshold

The next meaningful step is shadow operation against real runtime receipts, with no production authority:

`real workflow / freshness / browser receipts`
→ `adapter`
→ `Proof Spine observe-only`
→ compare with existing local decision

Promotion remains unjustified until the shadow evaluator prospectively catches or prevents at least one consequential state that the existing local system would otherwise leave live or materially ambiguous, with acceptable false-block and maintenance cost.

## Claim boundary

This field case proves that the previous Newsletter example was causally under-specified and that the two-tree contract better matches the repository's fail-closed product law. It does **not** prove that Proof Spine is production-ready, that every dependency has been modeled, that the later healthy run proves same-instant health for the skipped run, or that any real external action should yet consume these gates.
