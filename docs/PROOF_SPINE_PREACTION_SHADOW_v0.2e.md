# Proof Spine pre-action shadow — Newsletter v0.2e

**Date:** 2026-09-16  
**State:** NON_NORMATIVE EXPERIMENT / EVIDENCE ONLY / NO PRODUCTION AUTHORITY  
**Base main observed when branch was created:** `1af947d3be9f76ea963b4b293953dedb6729bb83`

This experiment advances the earlier Newsletter shadow pilot from **live-production health observation** into a second, separate question:

> Before a future Pages action, does the current `main` candidate already contain the native Story identities that Newsletter's canonical localization contract requires?

The producer still does not contain Proof Spine claims, gates, mission law, promotion logic, deployment logic, or publication authority.

## Why this exists

Newsletter has now produced more than one natural case in which Pages build/deploy/browser checks succeeded while the exact source state lacked required native editions and post-deploy localization health was red.

The first Proof Spine field analysis reconstructed that causal gap after the fact. The remaining discriminator is stricter: can a public-safe, unattended observer expose the invalid prerequisite **before a later consequential Pages action** without changing production behavior?

## Architecture

```text
current Newsletter main candidate
        ↓
Newsletter-owned localization integrity validator
        +
source-alignment proof against stable origin/main
        +
existing live-health + sanitized ARB synchronization observations
        ↓
public-safe v2 shadow receipt
        ↓
private Agent Hub reviewed proof contract
        ↓
WOULD OPEN / WOULD CLOSE only
```

The production gate remains Newsletter-owned. The shadow producer never exits non-zero merely because the candidate is incomplete.

## Candidate observation

`tools/proof_spine_preaction_shadow_receipt.py` reuses the earlier evidence adapter and executes:

```text
python tools/validate_localizations_partial.py \
  --site release-src \
  --i18n-dir site/data/i18n \
  --receipt <ephemeral path>
```

That validator already performs project-native structural/integrity work and emits the public-safe facts required here:

- canonical Story count;
- native-complete Story count;
- pending translation count;
- pending stable Story IDs;
- required locale set;
- deterministic state (`COMPLETE` or explicit backlog).

The wrapper normalizes only two positive observation states:

- `COMPLETE`;
- `INCOMPLETE_NATIVE_EDITIONS`.

Malformed, contradictory, unexecuted, or schema-unknown evidence becomes `UNKNOWN` rather than a false positive or false accusation.

**Footnote for future maintainers:** these are project observation states, not Proof Spine `VALID / INVALID` states and not release permission. The reviewed private contract performs that composition.

## Applicability / anti-zombie boundary

Candidate truth now expands the material source-alignment envelope to include:

- `LOCALIZATION.md`;
- `release-src`;
- `tools/validate_localizations_partial.py`;
- the existing Story/status/locale/health inputs from the first shadow pilot.

The receipt brackets all observations with `origin/main` alignment snapshots. If those material inputs differ, fetch fails, or `main` changes during observation, the receipt must not claim it represents the current-main candidate.

This matters because the shadow branch itself contains experimental files. The experiment is allowed to differ from `main` in its adapter/docs/workflow while only claiming candidate applicability when the **material product inputs** are identical.

## Authority separation

The receipt explicitly records that it did **not** observe:

- the independent six release gates as a substitute for their real machinery;
- publication authority.

Therefore even a `COMPLETE` localization observation cannot by itself produce an authorized deploy decision. Conversely, an incomplete native-edition observation is enough for the reviewed `all`-composed candidate contract to say **would close** without fabricating the unknown sibling prerequisites.

## Natural prospective target

At the time this branch was cut, production `main` was `1af947d3be9f76ea963b4b293953dedb6729bb83`.

That SHA had just completed Pages run `35138995503` successfully, followed immediately by production-health run `35139216281` with overall failure. The experiment does not count that already-finished deploy as prospective prevention.

The intended discriminator is the next naturally occurring Pages attempt on unchanged or later current `main`: if the shadow receipt has already established a source-aligned incomplete prerequisite before that action, the campaign has genuine **pre-action detection timing** evidence even though the shadow itself remains non-enforcing.

Do not manufacture a production failure or trigger a deploy merely to satisfy this criterion.

## Tests

`tests/test_proof_spine_preaction_shadow.py` pins the producer-side boundary:

1. complete coverage remains observational `COMPLETE`, never synthetic `VALID`;
2. one pending Story is immediately visible as `INCOMPLETE_NATIVE_EDITIONS`;
3. inconsistent counts become `UNKNOWN`;
4. unknown schema becomes `UNKNOWN`.

The private Hub adapter must independently prove the downstream composition and preserve live-site/candidate causal isolation.

## First executed current-main observation

Hosted workflow run `35140061610`, job `104942058126`, executed the complete pre-action producer path and finished `success`.

Observed at `2026-09-16T19:22:02.358706Z`:

- source alignment before/after: `MATCH`;
- represented current main: `1af947d3be9f76ea963b4b293953dedb6729bb83`;
- canonical Stories: `43`;
- native-complete Stories: `42`;
- pending native editions: `1`;
- pending Story: `FCMO-7EBD0FA07C12`;
- candidate state: `INCOMPLETE_NATIVE_EDITIONS`;
- live translation health: `FAIL`;
- serving, browser-surface, publication-freshness and editorial-freshness checks: `PASS`;
- all **4/4** producer regressions: `PASS`.

Artifact `10464627216` was downloaded and hashed independently:

- ZIP bytes: `3112`;
- ZIP SHA-256: `ff802fb3816c1c41ddd5ad897aa0c0b35d1180714b3bce5cf3215d2843d2507c`;
- inner JSON bytes: `10157`;
- inner JSON SHA-256: `61bd07a09ff31b648f566fcc6323daa193b1901394e2d1b2f12f23762be260d4`.

**Footnote for future maintainers:** keep these byte identities separate from semantic claims. An artifact hash proves which bytes were inspected; it does not create publication authority or make the proof contract correct.

## Timing result so far

The receipt was produced after the already-completed Pages run `35138995503`. A later exact-SHA Actions query found no subsequent deploy for the unchanged `1af947d3...` main state, and `main` remained on that SHA.

Therefore the supported result is narrower than prevention:

> the unattended observer executed successfully and detected the currently incomplete release prerequisite before any *future* action, but no later consequential Pages action has yet occurred against which to demonstrate a natural catch-before-action event.

Do not label this result `PREVENTED`, `BLOCKED IN PRODUCTION`, or `PROSPECTIVE INCIDENT CAUGHT` until a later natural action sequence actually supplies that evidence.