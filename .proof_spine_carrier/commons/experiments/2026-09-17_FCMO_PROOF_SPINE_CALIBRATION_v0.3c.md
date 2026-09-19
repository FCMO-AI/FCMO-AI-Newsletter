# FCMO Proof Spine v0.3c — decision calibration without action-selection bias

**Date:** 2026-09-17  
**State:** NON_NORMATIVE EXPERIMENT / EVIDENCE ONLY  
**Scope:** universal calibration semantics; v0.3b preserved as historical lineage

## Independence correction — adversarial BONK

A later adversarial pass found one remaining calibration leak: `PROJECT_LOCAL + INDEPENDENT_OF_SPINE` was still only metadata, so a project-local validator created *because Spine raised the defect* could be mislabeled as independent calibration evidence.

v0.3c now requires explicit adjudication-mechanism provenance. A scored independent label must come from either:

- `PREEXISTING_PROJECT_LOCAL` — a project-local mechanism demonstrably established no later than the gate observation; or
- `EXTERNAL_INDEPENDENT` — an independently reviewed external mechanism.

`SPINE_DERIVED` mechanisms remain useful repair/proof evidence but are `UNSCORABLE` for calibration. Contradictory metadata such as `INDEPENDENT_OF_SPINE + SPINE_DERIVED` is rejected rather than trusted.

This corrects the current continuity event: repair PR #44 was created downstream of the Spine finding, so run `35297040705` cannot independently calibrate Spine even though it truthfully re-proves the local defect. The first field event remains scoreable because Newsletter's pre-existing production-health mechanism had already executed and failed on the same defect at run `35139216281` before the 19:22Z Spine gate observation, and independently failed again after the later deploy.

Corrected field calibration: one independently adjudicated `TRUE_BLOCK`, one Spine-derived continuity event `UNSCORABLE`, one scored causal episode, sensitivity `1/1` with the same tiny-sample boundary, and specificity still `null`.

## Why v0.3c exists

The v0.3b ledger fixed retry inflation and zero-denominator theater, but adversarial review found three remaining ways calibration could lie:

1. action.occurred=false made a case UNSCORABLE, which would hide a false block precisely when future enforcement successfully prevented the action;
2. source_authority=PROJECT_LOCAL did not prove the later adjudication was independent of the Spine decision;
3. the case did not require a timestamped same-subject binding between the gate, any observed action, and the adjudication.

v0.3c fixes those semantics without rewriting v0.3b history.

## Universal v2 law

tools/proof_spine_calibration_ledger_v2.py separates two questions:

- Was the gate decision correct? Scored against later project-local adjudication explicitly marked INDEPENDENT_OF_SPINE and bound to the exact same subject.
- What happened to the action? Reported separately. An action may occur, be prevented, or remain absent without changing whether the prior gate was correct.

This means a future CLOSED + SHOULD_ALLOW remains a measurable FALSE_BLOCK even when enforcement prevented the action entirely.

Each scored case now requires:

- explicit subject;
- exact subject match in later adjudication;
- exact subject match in an observed action when one exists;
- adjudication timestamp not earlier than the gate observation;
- project-local authority;
- explicit relationship to Spine: INDEPENDENT_OF_SPINE, DERIVED_FROM_SPINE, or UNKNOWN.

Only INDEPENDENT_OF_SPINE enters the accuracy denominator. Relationship provenance is reviewed evidence metadata, not self-authenticating truth.

## Field migration

The first Newsletter case remains one real TRUE_BLOCK episode:

- shadow gate: CLOSED / INVALID at 2026-09-16T19:22:02.358706Z;
- later Pages action: 2026-09-16T21:21:42Z;
- lead time: 7179.641294 s;
- post-action project-local adjudication: health run 35152090698 at 2026-09-16T21:23:14Z;
- exact subject: source SHA 1af947d3..., obligation FCMO-7EBD0FA07C12.

The current continuity observation on Newsletter main 29cf44c... remains useful continuity/repair evidence, but it is UNSCORABLE for calibration because its adjudication mechanism is repair PR #44, which was created downstream of the Spine finding. It is preserved rather than silently dropped.

## Current calibration

- events: 1 TRUE_BLOCK + 1 UNSCORABLE Spine-derived continuity event;
- causally deduplicated scored episodes: 1;
- observed consequential actions: 1;
- sensitivity: 1 / 1;
- false-allow rate: 0 / 1;
- specificity denominator: 0 -> null;
- false-block denominator: 0 -> null.

No specificity claim exists yet.

## Newsletter repair evidence

Repair PR #44 was merge-forwarded onto current main without merging to production. After adding topology regressions and fixing the regressors themselves, hosted release-validation run 35297040705 executed 54 tests: 53 PASS / 1 FAIL. Both topology checks and all strict-vs-health tests pass. The sole red remains the real FCMO-7EBD0FA07C12 native-edition debt. Surface-contract run 35297040706 also passed.

The topology regression proves the strict local release gate appears before Pages candidate assembly/upload and that newsroom-health continues to execute health-SLO mode rather than the strict release mode.

## Promotion boundary

The missing empirical denominator remains a naturally healthy prospective episode: Spine says OPEN, later independent project-local adjudication says SHOULD_ALLOW, and no hidden invalid prerequisite is discovered. Because decision correctness is now independent of action occurrence, such a sample can still count even if a future local authority chooses not to perform the action for unrelated reasons.

A real FALSE_BLOCK must reduce specificity even when the block prevented the action. A real FALSE_ALLOW must reduce sensitivity even when the action later happened to succeed.

## Negative knowledge preserved

- action success is not release validity;
- action absence is not proof a block was correct;
- prevention must not make false blocks statistically invisible;
- PROJECT_LOCAL is authority provenance, not proof of independence from Spine;
- same repository/gate/episode is not enough: calibration needs same-subject binding;
- later means later: an adjudication predating the gate cannot score that gate;
- v0.3b remains historical evidence rather than being silently rewritten.
