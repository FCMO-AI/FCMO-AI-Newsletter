# FCMO Proof Spine — Exact-Head Validation Attempts v0.2b → v0.3

**Date:** 2026-09-14  
**Last materially updated:** 2026-09-15  
**Authority:** NON_NORMATIVE EVIDENCE NOTE  
**State:** `UNEXECUTED` — three hosted attempts failed before any job step began

## Purpose

Close the experiment's exact-snapshot evidence gap by running the Proof Spine regression suites and the portable Agent Hub integrity runner on the actual GitHub branch HEAD rather than on reconstructed source payloads.

## Attempt #1 — v0.2b

- Repository: `FCMO-AI/FCMO-Agent-Hub`
- Branch: `agent/proof-spine-v0.1`
- Attempted head: `69a877d7fd05f9937d169ec6b9fd49cce1196526`
- Workflow run: `34904535360`
- Check/job: `104178008925` (`exact-head-proof`)
- GitHub conclusion: `failure`
- Observed job payload: `steps = null`
- Decoded job logs: unavailable; the log retrieval route returned no runnable job log payload

## Attempt #2 — v0.3 universal-federation campaign / PR path

The v0.3 BONK briefly restored a read-only, path-scoped `pull_request` trigger because exact-head execution had become decision-relevant to the universalization campaign. The workflow included the generic engine suite, the new FCMO-wide federation suite, the Newsletter adapter regressions, and full Hub integrity.

- Repository: `FCMO-AI/FCMO-Agent-Hub`
- Branch: `agent/proof-spine-v0.1`
- Attempted head: `3e21d35211a1c41857e3a42d9b07dce6f6c843ed`
- Workflow run: `35033314130`
- Check/job: `104596603493` (`exact-head-proof`)
- GitHub conclusion: `failure`
- Observed job payload: `steps = null`
- Checkout/setup/test/integrity steps executed: **none**
- Decoded job logs: unavailable; the GitHub log endpoint returned a backing `BlobNotFound` response

## Attempt #3 — v0.3 branch-push discriminator

A later BONK tested a materially different event path instead of retrying the same PR mechanism. The workflow was temporarily scoped to `push` events on only `agent/proof-spine-v0.1` and only Proof-Spine-relevant paths. The purpose was diagnostic: distinguish an event-specific PR failure from a broader hosted-execution failure.

- Repository: `FCMO-AI/FCMO-Agent-Hub`
- Branch: `agent/proof-spine-v0.1`
- Attempted head: `4f82b47eeefd8e1d584348f923516c50c0f650e0`
- Workflow run: `35044247338`
- Check/job: `104630537501` (`exact-head-proof`)
- Event: `push`
- GitHub conclusion: `failure`
- Observed job payload: `steps = null`
- Checkout/setup/test/integrity steps executed: **none**

This third attempt matters because it falsifies the useful narrow hypothesis that the failure was specific to the PR event path. It does **not** identify the underlying hosting/root cause.

## Interpretation

None of the three hosted runs executed Proof Spine code or the Hub integrity runner. Therefore the correct evidence state remains:

> **`UNEXECUTED`, not `PASS`, and not a Proof Spine test `FAIL`.**

The combined observation now supports a narrower and stronger infrastructure statement: the presently available private-Hub hosted workflow path fails before step materialization across both PR-triggered and branch-push-triggered execution. It still does **not** establish why that hosting failure occurs.

A hosting-level red conclusion with `steps = null` cannot truthfully be promoted into evidence that the code failed its assertions. Equally, it cannot be treated as evidence that those assertions passed.

The current v0.3 federation/freshness source and regression suite therefore remain **unexecuted at exact Hub HEAD** as of this note.

## Resulting change

All automatic experiment triggers were removed again after attempt #3. The workflow remains available as a manual `workflow_dispatch` harness containing the full current test surface, including the focused universal temporal-integrity suite.

This avoids standing red checks that never reach checkout while preserving an exact-head route for a runner-bearing environment that can actually execute the job.

**Footnote:** removing the automatic trigger does not waive the validation debt. It keeps infrastructure failure from masquerading as proof failure; exact execution must still be earned elsewhere before promotion.

## Next adequate evidence

Any one of these can close the present execution gap:

1. a manual invocation of the branch workflow in an environment where its job steps actually execute;
2. an exact checkout of the current branch HEAD followed by:
   - `python tools/test_proof_spine_v2.py`
   - `python tools/test_proof_spine_federation.py`
   - `python tools/test_proof_spine_temporal_integrity.py`
   - `python tools/test_proof_spine_newsletter_v02b.py`
   - `python tools/test_proof_spine_newsletter_shadow.py`
   - `python tools/run_integrity.py --expect-commit <EXACT_HEAD> --receipt <OUTSIDE_REPO>`
3. another execution substrate that produces equivalently commit-bound receipts for the same checks.

## Claim boundary

This note proves only that three exact-head validation attempts were made through two materially different hosted event paths and that none of those jobs began its steps. It does not establish why the runner failed to start, does not establish source/test success or failure, does not prove the v0.3 federation implementation correct, and does not grant promotion authority.
