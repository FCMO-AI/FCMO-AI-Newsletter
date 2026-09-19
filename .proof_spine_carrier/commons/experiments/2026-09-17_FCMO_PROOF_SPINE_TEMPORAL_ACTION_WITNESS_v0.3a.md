# FCMO Proof Spine v0.3a — Temporal Action Witness + Obligation Memory

Status: **NON_NORMATIVE EXPERIMENT**  
Field system: `FCMO-AI/FCMO-AI-Newsletter`  
Hub PR: `FCMO-AI/FCMO-Agent-Hub#55`

## Why this BONK exists

The prior campaign had evidence that Proof Spine could describe a bad candidate before a later action, but it lacked a generic, contract-owned way to prove three things together:

1. the gate evaluation really existed **before** the external action;
2. the action concerned the **same declared subject**, not merely a nearby commit/repository;
3. an unresolved defect could not later look “resolved” merely because a bounded detector stopped returning it.

v0.3a closes those three holes without granting Proof Spine any execution or blocking authority.

## Universal capability 1 — temporal action witness

`tools/proof_spine_action_witness.py` evaluates:

```text
reviewed witness contract
        +
pre-action gate observation
        +
external action observation
        + optional post-action subject corroboration
        ↓
OBSERVATIONAL_ONLY temporal witness
```

The reviewed contract owns:

- gate identity;
- action kind;
- direct subject-binding keys;
- any additional continuity keys required for mutable/generated candidates;
- accepted action-time boundary preference.

Neither a proof receipt nor an action producer may self-declare what is “the same candidate.”

### Critical correction: commit identity is not artifact identity

A scheduled/generated build can consume mutable inputs while remaining on the same Git SHA. Therefore `repository + SHA` is not universally sufficient candidate identity.

The witness supports contract-required continuity keys. In the Newsletter field case the direct binding is:

- project id;
- repository;
- exact source SHA.

Material continuity is independently corroborated by:

- Story identity `FCMO-7EBD0FA07C12`;
- missing native locales `es-419` and `zh-Hans`.

Without that required corroboration, the same-SHA case deliberately becomes `SUBJECT_UNDERBOUND`, not a stronger causal claim.

## Natural prospective field event

The source-aligned pre-action shadow run `35140061610` emitted its receipt at:

`2026-09-16T19:22:02.358706Z`

It observed current Newsletter `main`:

`1af947d3be9f76ea963b4b293953dedb6729bb83`

with one incomplete native Story identity:

`FCMO-7EBD0FA07C12 -> missing [es-419, zh-Hans]`

The reviewed predeploy proof mapped that premise to:

`candidate_may_enter_deploy = CLOSED / INVALID`

A later **scheduled** Pages run on that exact source SHA, run `35151946023`, was created/started at:

`2026-09-16T21:21:42Z`

and completed all three consequential jobs successfully:

- `build` — success;
- `deploy` — success;
- `prove the deployed newspaper is actually live` — success.

The pre-action proof therefore existed **7,179.641294 seconds (1h 59m 39.641294s)** before the action boundary exposed by GitHub Actions `created_at`/`run_started_at`.

### Material continuity across the action

The immediately triggered production-health run `35152090698` checked out the same SHA. Its `translation-health` job `104982624915` failed at `2026-09-16T21:23:20Z` and emitted:

- state `UNHEALTHY_TRANSLATION_BACKLOG`;
- the same Story `FCMO-7EBD0FA07C12`;
- the same missing locales `es-419`, `zh-Hans`;
- age `27.687 h`.

The resulting generic witness classification is:

`PRE_ACTION_CLOSED_CORROBORATED`

This is the first natural field case in this campaign where the Proof Spine shadow result is demonstrated to have existed before a later consequential action and the material defect is independently observed across that action.

**It is not prevention evidence.** Proof Spine did not own the Pages gate and the deploy happened.

## Universal capability 2 — no-aging-to-green obligation memory

A second field effect exposed a different temporal trap.

Later, still on the same Git SHA, production-health run `35167278101` reported `translation-health = success`. Its output at `2026-09-17T00:37:08Z` was:

```json
{"fresh_window_hours": 30.0, "missing_recent": [], "overdue_count": 0, "state": "HEALTHY"}
```

No explicit translation-resolution evidence was observed. The previously missing Story was published at `2026-09-15T17:42:05.789766Z`; by this later check it had simply aged beyond the 30-hour health window.

This is not necessarily a defect in Newsletter's **health SLO**: PR #44 already distinguishes bounded health prioritization from strict release eligibility. It is, however, unsafe for a proof system to interpret detector disappearance as debt resolution.

`tools/proof_spine_obligation_memory.py` therefore adds the symmetric temporal law:

> An old PASS may not live forever through stale evidence, and a known OPEN obligation may not die merely because it falls out of a detector window.

A reviewed obligation contract owns:

- obligation identity keys;
- states that mean OPEN;
- states that count as explicit RESOLUTION.

Once an obligation is observed open:

- omission in later snapshots -> `ABSENT_BUT_CARRIED_OPEN`;
- unknown producer vocabulary cannot close it;
- an orphan `RESOLVED` event cannot manufacture reassuring history;
- only contract-recognized explicit closure evidence resolves it;
- a later recurrence after closure increments its generation.

For the real Newsletter sequence, the obligation memory remains:

`ACTIVE / unresolved`

after the later health detector returns `HEALTHY` with an empty recent set.

## Executed regression evidence

Local isolated execution against the exact new payload:

- `tools/test_proof_spine_action_witness.py` — **9/9 PASS**;
- `tools/test_proof_spine_obligation_memory.py` — **8/8 PASS**;
- `tools/test_proof_spine_newsletter_temporal_field.py` — **3/3 PASS**.

Total new focused coverage: **20/20 PASS**.

The field fixture is:

`commons/experiments/2026-09-17_FCMO_PROOF_SPINE_NEWSLETTER_TEMPORAL_FIELD_CASE_v0.3a.json`

It records normalized inputs and expected outcomes; it does not manufacture production authority.

## Relationship to Newsletter PR #44

Newsletter PR #44 remains the project-local repair candidate. It already encodes the right semantic separation:

- `HEALTH_SLO` may use bounded freshness/grace for operational health;
- `RELEASE_GATE --require-complete` checks every Story identity and must fail before Pages upload/deploy if native editions are incomplete.

v0.3a does not replace that local gate. It supplies evidence that the shadow had already diagnosed the bad premise before a later old-main deployment, and provides a generic temporal memory primitive so later green health cannot be misread as proof that the debt was repaired.

## What this changes in the promotion argument

The prior proof debt “demonstrate unattended pre-action detection before a consequential action” is now materially satisfied for one natural Newsletter case in **shadow** mode:

- unattended producer;
- source-aligned receipt;
- negative gate result;
- result timestamp earlier than later scheduled deploy;
- exact source binding;
- same material defect independently corroborated immediately after deploy.

What remains unresolved:

1. **No prevention evidence yet.** The project-local repair is still draft/unmerged, so the bad action was observed, not prevented.
2. **Hub exact-head hosted execution remains unavailable.** Current private-Hub Actions attempts have failed before any step; the new 20-test result is local isolated execution, not hosted exact-head proof.
3. **Specificity over repeated natural cycles** still needs evidence: false-block rate, maintenance burden, and behavior across healthy as well as unhealthy events.
4. **Obligation memory adoption is not automatic.** A project must define reviewed identity/open/closure semantics; absence can only be carried forward where persistent debt is actually the intended concept.

## New durable laws discovered

1. **Operational proximity is not causal dependency.**
2. **Repository identity is not necessarily artifact identity.**
3. **Commit identity is not necessarily candidate identity.**
4. **Observation absence is not resolution evidence.**
5. **Freshness and debt persistence are temporal duals:** stale positive evidence must expire; unresolved negative obligations must not evaporate without closure evidence.
6. **Prospective sensitivity and enforcement are separate claims.** A system can correctly know before an action while still lacking authority to stop it.

## Claim boundary

This record supports a natural **prospective shadow sensitivity** claim for the stated Newsletter event and demonstrates generic temporal primitives under focused local tests. It does not claim that Proof Spine prevented deployment, that PR #44 has been promoted/merged, that the private Hub exact-head suite ran successfully, or that Proof Spine should yet be canonical FCMO Governance.
