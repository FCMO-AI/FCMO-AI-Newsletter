# FCMO Proof Spine — Newsletter localization field divergence v0.2c

**Date:** 2026-09-15 America/Mexico_City / 2026-09-16 UTC  
**Authority:** NON_NORMATIVE FIELD EVIDENCE  
**Project:** `FCMO-AI/FCMO-AI-Newsletter`  
**Exact production source SHA:** `3783309c7cf5f43ac4fa8307fcb05fa2349991c4`  

## Why this case matters

This is the first naturally occurring Proof Spine field case in the current campaign where the missing causal edge was not merely theoretical.

Newsletter's canonical Product Goal says product success includes `EN/ES/ZH publication`, that localization contracts are fail-closed, and that production deployment runs only after the candidate passes. It also distinguishes successful deployment from actual product health.

The production implementation had the necessary localization oracle, but it was positioned only in post-deploy production health rather than in the Pages pre-deploy causal path.

That created a real sequence:

```text
exact source candidate has overdue native-locale backlog
        ↓
Pages build succeeds
        ↓
Pages deploy succeeds
        ↓
live browser oracle succeeds
        ↓
post-deploy health runs same project-owned translation oracle
        ↓
translation-health FAIL
```

The problem was not that Newsletter lacked the truth. The problem was that the truth arrived **after the action whose prerequisite it should constrain**.

## Exact field evidence

### Candidate / source state

Main remained at:

`3783309c7cf5f43ac4fa8307fcb05fa2349991c4`

Committed `site/data/newsroom-status.json` on that SHA already recorded:

- `pending_translation_count = 1`;
- `pending_translation_ids = ["FCMO-7EBD0FA07C12"]`;
- `translation_state = "DEGRADED_TRANSLATION_BACKLOG"`;
- translation counts `42 / 42` against `43` canonical stories.

### Successful deploy

GitHub Actions run `35039908916` (`Deploy FCMO AI Newsletter`) executed on the same source SHA.

Observed jobs:

- `build` — **success**;
- `deploy` — **success**;
- `prove the deployed newspaper is actually live` — **success**.

The build included browser/runtime/homepage/surface checks, but did not execute `tools/translation_health.py` as a pre-deploy prerequisite.

### Immediately triggered production health

Workflow-run-triggered health run `35040081111` executed after that successful deploy on the same source SHA.

Jobs:

- `serving-health` — **success**;
- `publication-freshness` — **success**;
- `editorial-freshness` — **success**;
- `translation-health` — **failure**.

The failing command was the existing Newsletter-owned oracle:

```text
python tools/translation_health.py --grace-hours 1 --fresh-window-hours 30 --minimum-importance 4
```

Its structured result was:

- state: `UNHEALTHY_TRANSLATION_BACKLOG`;
- research id: `FCMO-7EBD0FA07C12`;
- importance: `6`;
- published: `2026-09-15T17:42:05.789766Z`;
- age at check: `6.759 h`;
- missing: `es-419`, `zh-Hans`;
- configured reconciliation grace: `1 h`.

Therefore the localization condition was not marginally crossing its boundary during the two-minute post-deploy interval. The story was already more than six hours old; on unchanged source bytes, the same oracle's one-hour grace had expired long before run `35039908916` entered deployment.

### Independent Newsletter-native test confirmation

Opening the local repair PR caused the repository's existing `Validate FCMO Newsletter Release` workflow to run on GitHub's actual merge checkout.

Run `35045885148`, job `104635478830`:

- checkout/compile — **PASS**;
- forbidden legacy translation/provider scan — **PASS**;
- repository test discovery — **47 PASS / 1 FAIL**;
- the sole failing test: `test_refresco_diario.RefrescoDiario.test_todo_lo_publicado_tiene_ediciones_nativas`;
- its failing subprocess: `verificar_traduccion.py`;
- same research id: `FCMO-7EBD0FA07C12`;
- same missing locales: `es-419`, `zh-Hans`;
- observed age at that later run: `8.206 h`;
- state: `UNHEALTHY_TRANSLATION_BACKLOG`.

This matters because it independently confirms the interpretation through **Newsletter's own existing regression suite**, not through a new Proof Spine rule. The repair PR's one-line causal relocation did not manufacture the red state; the repository was already red on precisely the localization contract the Pages path had failed to consume.

Do not “fix” this validation red by weakening or bypassing the test. It is truthful evidence of the production condition that the pre-deploy path should respect.

## Causal correction

The field case requires a pre-action distinction that v0.2b did not represent explicitly:

```text
candidate release proof
        +
candidate localization proof
        ↓
CANDIDATE MAY ENTER DEPLOY
        ↓
Pages deployment
        ↓
post-deploy browser + health
        ↓
ADVANCE CURRENT EDITION
```

The new experimental contract is:

`2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_PROOFSPEC_v0.2c.json`

It adds the primitive evidence node:

`candidate_localization_ready`

and the explicit pre-action gate:

`candidate_may_enter_deploy`.

The exact field receipt is:

`2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_FIELD_RECEIPT_v0.2c.json`

The receipt deliberately leaves upstream/release/publication-authority premises `UNKNOWN`; a green Pages run is not laundered into proof that those independent prerequisites passed. Localization is independently `FAIL`, which is sufficient to make the `all`-composed pre-deploy gate `INVALID / CLOSED`.

## Concrete project repair

A separate Newsletter draft PR was created:

`FCMO-AI/FCMO-AI-Newsletter#44`

It does not give Proof Spine deployment authority. Instead it moves the **existing project-owned oracle** into `pages.yml` before Pages candidate assembly/upload:

```text
python tools/translation_health.py --grace-hours 1 --fresh-window-hours 30 --minimum-importance 4
```

Expected local behavior:

- native coverage complete → proceed;
- missing locale still inside the already-established one-hour reconciliation grace → proceed under existing policy;
- overdue material localization backlog → stop before Pages artifact/deploy and preserve the previous public edition.

This is the desired institutional pattern:

> **Spine identifies the missing causal dependency; project-local law owns the repair and enforcement mechanism.**

## What this proves

This field case materially establishes **real sensitivity**:

1. a consequential project prerequisite was already invalid;
2. the local project possessed an oracle capable of proving that invalidity;
3. the action path did not consume that oracle before deployment;
4. deployment and live-browser checks nevertheless succeeded;
5. a causally complete Proof Spine contract closes the pre-deploy gate on the failed prerequisite;
6. the same interpretation is independently reproduced by Newsletter's pre-existing test suite;
7. the finding produced a concrete local repair rather than only another observation artifact.

## What this does **not** prove

Do not over-promote this case.

- Proof Spine did **not** prevent run `35039908916`; the deployment had already completed before this field analysis.
- The new Hub field regression is not yet exact-head executed because the private Hub runner still fails before checkout.
- Newsletter PR #44 is draft and unmerged; production has not yet demonstrated the repaired pre-deploy behavior.
- PR #44's current red validation is the pre-existing localization failure itself, not evidence that the one-file Pages change is defective; the downstream workflow stops at the truthful failing repository test before later validation stages.
- One true-positive field divergence does not establish an acceptable false-block rate or maintenance burden.
- This does not grant the Hub, Proof Spine, or any adapter authority to deploy, roll back, publish, merge, or release.

The strongest truthful status is therefore:

> **Naturally occurring sensitivity is now demonstrated and it caused a project-local repair candidate; unattended prospective prevention is not yet demonstrated.**

## Promotion consequence

The prior promotion debt item “find a consequential invalid/stale/unknown prerequisite that current local machinery would otherwise leave live or materially ambiguous” is no longer purely hypothetical.

Replace it with the stricter remaining requirement:

> demonstrate that the shadow/contract can detect such a divergence **before the consequential action** in unattended operation, with acceptable false blocks and maintenance burden.

That is the next evidence threshold. It is smaller and sharper than the previous open-ended search for any sensitivity event.
