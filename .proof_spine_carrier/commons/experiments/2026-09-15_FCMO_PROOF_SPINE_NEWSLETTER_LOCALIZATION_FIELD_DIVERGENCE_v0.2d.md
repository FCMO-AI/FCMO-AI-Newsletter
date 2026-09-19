# FCMO Proof Spine — Newsletter localization field divergence v0.2d

**Date:** 2026-09-15 America/Mexico_City / 2026-09-16 UTC  
**Authority:** NON_NORMATIVE FIELD EVIDENCE  
**Project:** `FCMO-AI/FCMO-AI-Newsletter`  
**Exact production source SHA:** `3783309c7cf5f43ac4fa8307fcb05fa2349991c4`  
**Supersedes for current interpretation:** `2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_FIELD_DIVERGENCE_v0.2c.md`  

## Correction from v0.2c

The first field pass correctly found a causal divergence but initially treated Newsletter's one-hour translation-health grace as if it were also release permission. Further repository-law inspection falsified that interpretation.

The authority hierarchy is explicit:

- `AGENTS.md` makes `PRODUCT_GOAL.md` canonical and requires `LOCALIZATION.md` when translation is in scope;
- `AGENTS.md` says a localization gate must not be weakened merely to make deployment green;
- `PRODUCT_GOAL.md` defines product success through `EN/ES/ZH publication` and requires last-known-good behavior when localization proof fails;
- `LOCALIZATION.md` states that every canonical public record requires Spanish + Simplified Chinese coverage and that **a new Story without both editions is a release failure, not permission to publish English-only**;
- `HANDOFF.md` repeats that a candidate failing localization must leave the previous known-good public release live.

Lower-level implementation comments had drifted toward “English may publish while native editions reconcile.” That is useful as a **candidate/source health observation model**, but it cannot override the canonical release contract.

The corrected distinction is:

```text
candidate/source translation backlog
        ↓
HEALTH SLO may use bounded grace for diagnosis/reconciliation
        ↓
RELEASE GATE has zero grace: every Story requires ES + ZH
        ↓
only complete candidate may enter Pages deployment
```

The v0.2c file is retained as experiment lineage; this v0.2d note is the corrected current interpretation.

## Naturally occurring divergence

On source SHA `3783309c7cf5f43ac4fa8307fcb05fa2349991c4`, committed status already reported:

- `canonical_story_count = 43`;
- `es-419 = 42`;
- `zh-Hans = 42`;
- `pending_translation_count = 1`;
- pending Story `FCMO-7EBD0FA07C12`;
- `translation_state = DEGRADED_TRANSLATION_BACKLOG`.

Despite that source state, Pages run `35039908916` completed:

- build — **success**;
- deploy — **success**;
- deployed live-browser oracle — **success**.

The immediately triggered health run `35040081111` then produced:

- serving-health — **success**;
- publication-freshness — **success**;
- editorial-freshness — **success**;
- translation-health — **failure**.

The failing Newsletter-owned health oracle reported:

- Story `FCMO-7EBD0FA07C12`;
- importance `6`;
- both `es-419` and `zh-Hans` missing;
- age `6.759 h`;
- health-SLO grace `1 h`.

The significant fact is not merely that the health grace expired. The exact candidate lacked native editions that canonical release law requires **before publication at all**.

## Independent repository confirmation — strict mode

Draft repair PR `FCMO-AI/FCMO-AI-Newsletter#44` caused the existing release-validation workflow to execute on GitHub's actual merge checkout after the repair had separated health and release semantics.

Final strict validation run `35046797664`, merge ref `5233df99d14d9d1964930750d07836c4196263ce`, head `65ad4b69b69e5e00549263d57f57b5590b366d46`:

- checkout/compile — PASS;
- provider/publisher boundary scan — PASS;
- tests executed — `52`;
- tests passed — `51`;
- tests failed — `1`;
- all four new strict-vs-health separation regressions — PASS;
- sole remaining failure — `test_todo_lo_publicado_tiene_ediciones_nativas`;
- same Story `FCMO-7EBD0FA07C12`;
- same missing `es-419`, `zh-Hans`;
- release oracle mode — `RELEASE_GATE`;
- release oracle state — `UNHEALTHY_TRANSLATION_INCOMPLETE`;
- `grace_hours = 0.0`;
- `fresh_window_hours = null`;
- backlog age by then — `8.438 h`.

The separate autonomous surface validation run `35046797658` completed **successfully** end-to-end. That isolates the red to localization completeness rather than broad candidate/surface breakage introduced by the repair.

This matters because the field conclusion is not a Proof Spine invention. Newsletter's own strict, zero-grace release oracle independently identifies the same source state as invalid while unrelated surface checks remain green.

## What Proof Spine contributed

Newsletter already possessed the facts and validators. The missing capability was causal composition.

Old effective topology:

```text
candidate source
   ├─ Pages build/deploy/browser checks ──> SUCCESS
   └─ localization health ────────────────> FAIL (after deployment)
```

Canonical topology:

```text
candidate release prerequisites
        +
strict native-edition completeness
        ↓
CANDIDATE MAY ENTER DEPLOY
        ↓
Pages build / deploy
        ↓
post-deploy browser + health
        ↓
ADVANCE CURRENT EDITION
```

The experimental field proof contract is:

`2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_PROOFSPEC_v0.2c.json`

The updated evidence-only field receipt is:

`2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_FIELD_RECEIPT_v0.2c.json`

That receipt intentionally leaves unrelated upstream/release/publication-authority premises `UNKNOWN`. It does not infer them from a successful deploy. `candidate_localization_ready = FAIL` is independently established, so the `all`-composed `candidate_may_enter_deploy` gate is necessarily `INVALID / CLOSED` regardless of the unknown siblings.

## Project-local repair candidate

Newsletter draft PR `#44` keeps Proof Spine out of production authority and repairs the local causal path instead.

### Explicit health vs release modes

`tools/translation_health.py` now distinguishes:

- default `HEALTH_SLO` — material/freshness prioritization + bounded reconciliation grace for operations;
- `--require-complete` / `RELEASE_GATE` — every Story identity must exist in both native editions; no grace, no importance/freshness exemption.

### Pages strict precondition

Before candidate assembly/upload, `pages.yml` now runs:

```text
python tools/translation_health.py --require-complete
```

Existing curated-i18n/application validators continue to own field/shape/content/source-identity checks. The new strict step closes the missing Story-identity completeness edge; it does not replace those validators.

### Publication oracle alignment

`tests/oraculos/verificar_traduccion.py`, whose job is to prove that published Stories have native editions, now also uses the same strict `--require-complete` mode. The one-hour grace remains only in `newsroom-health.yml` as an operations/health signal.

This removes the previous semantic split where a release-oriented test name could silently inherit health-SLO grace.

### Regression proof

`tests/test_translation_health.py` proves:

1. health mode may report a just-created missing Story inside grace without calling health failed;
2. strict release mode rejects that exact same Story immediately;
3. strict release mode catches missing Story identities that health prioritization would intentionally ignore because they are old/low-importance;
4. strict release mode accepts complete native identity coverage.

All four passed on the final strict-validation head.

## Secondary finding: authority drift is itself a failure mode

This BONK exposed a general Proof Spine lesson beyond Newsletter:

> **A dependency graph can be wrong even when every local check is individually correct, because lower-level implementation semantics may drift away from the authoritative contract they are supposed to realize.**

For this case:

- canonical law said complete EN/ES/ZH before release;
- source/backlog health machinery evolved a useful grace concept;
- comments began describing that health grace as if it were publication policy;
- a release-oriented oracle also inherited the health grace;
- Pages never consumed the strict canonical dependency;
- a successful deployment therefore coexisted with a canonical release violation.

The correct response is not to make Spine a global policy oracle. It is to bind proof contracts to reviewed project authority and use field mismatches to repair the local implementation.

## What this proves

This case now supports a materially stronger statement than the earlier synthetic work:

1. a real production source state violated a canonical project prerequisite;
2. the project already possessed machine-readable evidence of the violation;
3. the consequential action path omitted that prerequisite;
4. the action nevertheless completed successfully;
5. post-action project health and independent strict repository CI both reproduced the missing prerequisite;
6. unrelated autonomous surface validation remained healthy, isolating the failed dimension;
7. a causally complete Spine contract would close the pre-action gate without laundering unrelated unknowns into PASS;
8. the finding generated a concrete, project-owned repair with executed regression coverage.

This is **real sensitivity evidence**.

## What this still does not prove

- Proof Spine did not prevent run `35039908916`; diagnosis happened after the naturally occurring deployment.
- Hub exact-head regression execution remains unproven because the private Hub hosted runner still dies before checkout.
- Newsletter PR #44 is draft/unmerged and current main still lacks the required native editions.
- The repaired production path has not yet completed a real unattended cycle after the missing editions are supplied.
- One true-positive divergence does not establish a low false-block rate or acceptable long-term maintenance cost.
- No Hub/Spine component receives publish/deploy/rollback/merge authority from this experiment.

The strongest current statement is:

> **Proof Spine has now demonstrated natural field sensitivity and caused a project-local causal repair; unattended pre-action prevention and operating economics remain unproven.**

## Promotion frontier

The old open-ended question “can Spine ever find a consequential validity problem?” is materially answered by this case.

The next useful discriminator is narrower:

> Can the same architecture observe and close a real invalid/stale/unknown dependency **before** the consequential action in unattended operation, while natural healthy cycles remain unblocked and adapter/contract maintenance stays acceptably small?

Do not inject artificial production breakage to satisfy that criterion.
