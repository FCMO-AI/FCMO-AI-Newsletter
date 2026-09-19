# FCMO Proof Spine — Recursive PARETOBONK v0.3h

**Date:** 2026-09-18  
**Authority:** NON_NORMATIVE_EVIDENCE  
**Branch:** `agent/proof-spine-v0.1`  
**PR:** #55  
**Method:** recursive PARETOBONK under the Agent Hub v1.3 doctrine  
**Status:** **STOPPED / NOT SATURATED — exact-head execution remains externally blocked before checkout; prospective calibration evidence is still required.**

> This note records engineering and falsification evidence. It does not promote Proof Spine, redefine project-local truth, grant action authority, or convert unexecuted tests into passing evidence.

## Mission lock

The objective of this recursive pass was not to add surface area. It was to repeatedly identify the highest-value remaining way Proof Spine could produce a misleadingly strong decision or calibration claim, fix that failure class, and then attack the newly exposed bottleneck.

Success for this pass therefore required:

- preserving project-owned semantics and authority boundaries;
- making mutable OPEN decisions temporally coherent rather than historically true;
- making calibration resistant to omission, relabeling, pooling, retry/episode gaming, and contract-version inheritance;
- binding calibration to exact executed decision bytes rather than hash-shaped prose;
- preserving exact receipts through real project adapters instead of generating and discarding them;
- refusing to claim a test PASS when the private Hub runner never reached a test step.

## Starting point

The branch already contained v0.3g preregistration work and the v0.3f BLM falsification that showed a structurally green gate could remain OPEN while project-local reconciliation had already invalidated the action. The coherent decision-cut / decision-lease repair was therefore the starting architecture, not the conclusion.

The preregistered v0.3g natural-calibration plan covered:

1. Newsletter `candidate_may_enter_deploy`
2. Newsletter `represent_live_production_healthy`
3. BLM `shadow_admit_blm_primary_execution`

Its exact plan bytes were Git-registered before future qualifying events, but the then-current calibration ledger still depended on an analyst-supplied case list.

## Recursive bonk ledger

### BONK 1 — hidden mutable dependency outside the lease surface

**Failure mode:** a primitive evidence dependency could feed a mutable gate while remaining absent from `required_evidence`. The original decision-cut validator only demanded reviewed freshness for required surfaces, leaving a possible zombie enabling path.

**Initial repair:** require the cut to cover the gate's transitive primitive dependencies.

**Recursive falsification of the repair:** exact equality would overconstrain legitimate `any` / `at_least` alternatives by making optional branches mandatory.

**Surviving repair:** keep `required_evidence` as the presence contract, but require *every primitive dependency capable of enabling a mutable gate* to be either explicitly stable or covered by reviewed freshness. Optional alternatives may remain optional; they may not escape the lease clock.

Key commits: `84db3cf`, `26f8cb0`, refined by `94a7ee2`, `16e4333`.

### BONK 2 — preregistered plan, post-hoc case omission

**Failure mode:** v0.3g could prove that a plan existed before the outcome, but an analyst could still submit only favorable future cases. “ALL_QUALIFYING_FUTURE_EVENTS” was a promise without an independently enumerable denominator.

**Repair:** calibration v6 adds source-enumerated coverage frames keyed by exact plan/project/repository/gate. Every decision-receipt digest enumerated by that frame must appear in the submitted cases. Missing or unexpected events make the whole frame denominator-incomplete.

Key commits: `9e9ceb5`, `f3dea18`, `50a5d35`.

### BONK 3 — fake completeness by prose-only enumeration

**Failure mode:** an enumeration object could claim completeness without pinning the source snapshot it supposedly enumerated.

**Repair:** every coverage frame now carries a canonical SHA-256 snapshot digest and an explicit source-event count that must equal the enumerated digest set. This does not make the external enumerator infallible; it makes the claimed snapshot byte-addressable and internally falsifiable.

Key commits: `a829851`, `1957e5c`.

### BONK 4 — calibration required a decision receipt the executor did not emit

**Failure mode:** calibration had evolved to demand `FCMO_PROOF_SPINE_DECISION_RECEIPT`, but the universal project/federation evaluator emitted no such object. The scientific contract and the runtime protocol were disconnected.

**Repair:** the universal evaluator now emits an evidence-only decision receipt binding:

- execution mode and evaluation time;
- project/federation context;
- exact proofspec digest;
- exact source-evidence digest;
- exact effective-evidence digest;
- proof-report digest;
- exact gate decisions.

The receipt deliberately excludes a circular self-hash; callers emit the canonical receipt digest beside it.

Key commits: `ba34766`, `d653c62`.

### BONK 5 — digest dialect incompatibility

**Failure mode:** the core engine's historical digest helper returns raw 64-character hex, while calibration requires canonical `sha256:<hex>`. The newly emitted receipt would therefore have been structurally incompatible with its consumer.

**Repair:** add `canonical_sha256()` for cross-component protocol fields while preserving legacy raw digest fields for compatibility.

Key commits: `0add800`, `229397f`.

### BONK 6 — hash-shaped provenance without the referenced bytes

**Failure mode:** calibration could validate that a decision-receipt digest *looked* like SHA-256 without possessing the exact receipt bytes.

**Repair:** v6 now consumes the actual universal decision receipts, recomputes their canonical digest, and cross-checks proofspec digest, effective evidence digest, evaluation time, gate id, and gate decision. Missing receipt bytes make the event UNSCORABLE; contradictory bytes fail hard.

An end-to-end regression now has the universal evaluator emit a real receipt which calibration consumes directly, avoiding hand-authored execution hashes.

Key commits: `b77091a`, `8c9984d`, `809302e`.

### BONK 7 — pooled rates hiding unobserved gates

**Failure mode:** one global sensitivity/specificity could let a high-volume or easy gate dominate while a critical registered gate had no scoreable evidence.

**Repair:** every preregistered plan/project/repository/gate is now a first-class calibration stratum, including zero-evidence strata. The aggregate is explicitly a micro description of observed decisions and cannot substitute for gate-level evidence.

Key commits: `15dffed`, `951c425`.

### BONK 8 — valid receipt, wrong project or subject

**Failure mode:** exact receipt bytes could still be relabeled onto another project or another concrete subject sharing the same gate name.

**Repair:** scoreable executed cases must use project-scoped decision receipts whose project id/repository match exactly and which share at least one concrete subject identity key with the case. Shared subject keys must agree. No overlap yields `DECISION_SUBJECT_UNDERBOUND`; mismatches fail hard.

Key commits: `9896244`, `7dce3e7`.

### BONK 9 — omit the entire hard gate

**Failure mode:** v6 initially protected events *inside* a coverage frame but did not require every registered gate to have a frame. “Zero events happened” and “we never enumerated this gate” were indistinguishable.

**Repair:** every registered gate needs an explicit source-enumerated frame, including an empty frame when the source genuinely observed zero qualifying events. Missing frames withhold aggregate headline rates. Raw observed micro statistics remain diagnostic only.

Key commits: `7be3b74`, `2bae059`.

### BONK 10 — analyst-controlled episode denominator

**Failure mode:** `episode_id` is case-authored. Errors could be merged into one episode while successes were split into many, manipulating an episode-based headline denominator.

**Repair:** headline accuracy now uses unique source-enumerated executed decision receipts. The same receipt cannot be counted twice under different case or episode ids. Episode deduplication remains only as a diagnostic view.

During self-review this change exposed and repaired an initialization-order defect before it could be represented as working evidence.

Key commits: `27478bb`, repair `bb4f586`, regression `a1ba94b`.

### BONK 11 — selective right truncation across gates

**Failure mode:** every gate could have a coverage frame while the difficult gate stopped observation earlier than the easy gate.

**Repair:** gates within one calibration plan must share a coherent `observed_through` horizon for aggregate headline rates. Unequal right-edge horizons retain the raw diagnostic mixture but withhold the headline.

Key commits: `231353f`, `3d3df12`.

### BONK 12 — contract revision inheritance

**Failure mode:** a stable `gate_id` can outlive changes to its proofspec. Pooling old and new contract revisions would let a changed gate inherit the statistical reputation of earlier logic.

**Repair:** scoreable decision events are tracked by proofspec digest inside each registered gate. Mixing multiple proofspec revisions within one gate withholds the aggregate headline and exposes the revision set.

Key commits: `fc7dc23`, `f218357`.

### BONK 13 — runtime generated evidence then discarded by an adapter

**Failure mode:** the Newsletter shadow adapter invoked the universal evaluator, which now generated exact decision receipts, but then dropped those receipts from its own output. Calibration would still starve despite correct core behavior.

**Repair:** Newsletter shadow output now preserves both live-health and predeploy universal decision receipts plus their canonical digests. Its normalized project scope also preserves `source_sha` as a generic subject identity key without deleting the historical `source_head_sha` field.

Key commits: `0db68e1`, `f05ea39`.

### BONK 14 — self-falsification of the bonk implementation

Two implementation defects were found by re-reading the exact modified code rather than trusting the patch intent:

1. a textual test-fixture replacement accidentally changed the preregistered plan's literal gate id to an undefined helper variable;
2. the aggregate-withholding logic was calculated but the report boundary still returned direct rates, effectively computing the alarm and ignoring it.

Both were corrected before this note.

Key commits: `e97d646`, `f9c5a90`.

## Current v0.3h calibration contract

A headline rate is now eligible only when all of the following hold:

1. the sampling plan is outcome-blind and its exact bytes are Git-verified before the event;
2. the event is prospectively enrolled under that plan;
3. the gate execution has exact universal decision-receipt bytes;
4. those bytes cryptographically match the case's proofspec/effective-evidence/time/gate/decision provenance;
5. project identity and at least one concrete subject identity key bind the receipt to the case;
6. the gate has a source-enumerated coverage frame;
7. every receipt enumerated by that frame is represented exactly once for that gate;
8. no unexpected receipt is smuggled into the frame;
9. the frame's claimed source snapshot is byte-addressed and count-consistent;
10. every gate registered by the plan has a frame, including explicit zero-event frames;
11. gates in one plan share a coherent right-edge observation horizon for aggregate reporting;
12. a registered gate is not mixing multiple proofspec revisions;
13. the independent adjudication / measurement-root rules inherited from v4/v5 still hold.

Headline rates use **unique source-enumerated decision events**. Episode grouping is diagnostic only.

## Exact-head execution evidence

A one-shot same-repository PR trigger was added solely to test the current head, then removed immediately after observation.

- workflow run: `35402305862`
- job: `105784622627`
- conclusion: `failure`
- executable steps: none / empty

This reproduces the same pre-step failure signature already recorded for four previous private Hub attempts. The run never reached checkout or Python, so it is **not evidence that the Proof Spine tests failed**.

The workflow comment now records all five failed-before-step attempts and has returned to `workflow_dispatch` only.

A second independent attempt to use Hugging Face Jobs for Python execution returned HTTP 402 / payment required. That also produced no test result.

## What is *not* proved

Do not infer any of the following from this pass:

- that v0.3h tests pass on an executable runner;
- that the external source enumerator is truthful merely because its snapshot is hashed;
- that Proof Spine has calibrated sensitivity/specificity yet;
- that retrospective historical cases can enter the headline denominator;
- that a zero-event frame proves future performance outside its stated observation window;
- that a project adapter gains deployment, scheduling, scientific-promotion, or publication authority by carrying a decision receipt.

## Highest-value next evidence

The next valuable work is no longer another generic rule.

1. Execute the exact branch head on a runner that actually reaches checkout/Python.
2. Wire source-native coverage producers for the preregistered Newsletter and BLM gates so empty and non-empty frames are generated from real platform/project event indexes rather than authored after the fact.
3. Collect the first prospective post-registration decision receipts and independent adjudications.
4. Evaluate per-gate and per-proofspec strata before interpreting any pooled statistic.
5. Only after real prospective evidence exists should further calibration machinery be justified by a concrete falsification.

## Recursive PARETOBONK disposition

**STOPPED / NOT SATURATED.**

The recursive pass materially reduced several independent overclaim paths, but truthful saturation cannot be claimed while:

- the current head has not executed on a functioning runner; and
- the preregistered gates do not yet have source-native prospective v6 coverage/decision evidence.

The correct continuation is therefore evidence acquisition and exact-head execution, not ceremonial hardening.
