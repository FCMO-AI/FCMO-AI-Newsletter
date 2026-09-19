# FCMO Proof Spine v0.3b — calibration ledger field note

**Date:** 2026-09-17  
**State:** NON_NORMATIVE EXPERIMENT / EVIDENCE ONLY  
**Scope:** universal calibration machinery, with Newsletter as one field sample

## Why this BONK exists

Proof Spine had gained a real pre-action catch, but the promotion question still had an easy way to become dishonest: repeated retries of one unresolved defect could be counted as many successes; Spine could grade itself; and a missing healthy comparison could be presented as a 0% false-block rate. v0.3b closes those failure modes.

## Universal calibration contract

`tools/proof_spine_calibration_ledger.py` compares the prior gate decision, whether a consequential action actually occurred, and later adjudication from **project-local authority/evidence**, never Proof Spine itself. The headline unit is a **causal episode**, not a workflow run. Repeated retries remain visible as event evidence but do not manufacture independent sensitivity/specificity.

A zero denominator stays `null`; it is never rendered as 0%.

## Current field result

The first scored episode is the natural Newsletter localization case: observer run `35140061610` said `CLOSED / INVALID` at `2026-09-16T19:22:02.358706Z`; Pages run `35151946023` began at `2026-09-16T21:21:42Z`; lead time was `7179.641294 s`; project-local health run `35152090698` independently found the same `FCMO-7EBD0FA07C12` missing `es-419` and `zh-Hans`; adjudication is `SHOULD_BLOCK`. This is one `TRUE_POSITIVE` causal episode.

Newsletter later advanced to `29cf44c997db38ce1fe37b537ccdaaa9226a0911`. The evidence-only observer was merged forward and re-executed as run `35295188707`: source alignment `MATCH`, 43 canonical / 42 complete Stories, same pending Story, `INCOMPLETE_NATIVE_EDITIONS`, serving/publication/browser checks PASS, editorial freshness FAIL, and translation-health PASS only because its 30h window aged the known defect out. Artifact `10528065876` has ZIP SHA-256 `eec505b7bbe68539a71350124e4f18619b17a11766607dd183575b929faa46b1`; exact receipt JSON SHA-256 is `3cd8decf0a90bb7b7dc880d2e366adf6d2542eae0b49067d393f50b648ba0b1d` (9628 bytes). This is the **same causal episode**, so it is `UNSCORABLE` as a new accuracy datapoint.

Two project-local surfaces still reject the obligation: PR #45 release validation `35295063488` fails strict localization integrity for the same ID; rescued repair PR #44 run `35295005452` executes 52 tests, 51 PASS / 1 FAIL, with all 4 strict-vs-health regressions PASS and the sole failure `UNHEALTHY_TRANSLATION_INCOMPLETE` for the same Story at ≈55.668h. #44 is mergeable again but remains draft/unmerged.

## Calibration today

- scored causal episodes: `1`
- true positive: `1`
- miss: `0`
- true negative: `0`
- false block: `0`
- sensitivity: `1 / 1`
- specificity: denominator `0` → `null`
- false-block rate: denominator `0` → `null`

The 1/1 sensitivity is a real field result but a tiny sample, not a universal percentage claim.

## Promotion boundary

The remaining discriminator is explicit: observe at least one naturally healthy prospective episode where Spine says `OPEN`, project-local evidence later says `SHOULD_ALLOW`, and the consequential action succeeds without a hidden invalid prerequisite. Only then does the specificity / false-block denominator begin to exist. A later `CLOSED + SHOULD_ALLOW` episode must count as a false block, however cautious it looked at the time.

## Negative knowledge preserved

- workflow-run count is not sample size;
- retries of one unresolved obligation are not independent confirmations;
- `no false blocks observed` is not `false-block rate = 0%`;
- a bounded health detector aging an item out is not closure evidence;
- project-local law adjudicates correctness; Proof Spine may not grade itself.
