# FCMO Proof Spine calibration v0.3e — measurement-path independence

**Date:** 2026-09-18  
**State:** NON_NORMATIVE EXPERIMENT  
**Scope:** FCMO-wide calibration integrity; no project action/release authority

## Why this pass exists

v0.3d closed one serious calibration loophole: only executed, byte-addressed Proof Spine gate decisions may enter accuracy denominators. A further loophole remained. A later project-local adjudicator could still reuse the **same observation mechanism** that supplied the gate and be called independent merely because the second invocation happened later.

That measures self-consistency, not independent sensitivity/specificity.

## v0.3e rule

A scoreable episode now requires all of the following:

1. the Spine gate was actually executed and bound to exact proofspec, effective-evidence and decision-receipt digests;
2. the later adjudication is project-local and causally independent of Spine;
3. gate and adjudicator are bound to the exact same subject;
4. **their measurement-root sets are disjoint.**

The last requirement does not demand different world state. Two instruments may observe the same subject and still be independent. It prevents asking the same checker twice and treating agreement as calibration.

## Field reclassification

The three preserved Newsletter cases remain historically useful, but none enters an accuracy denominator:

- first native-edition pre-action catch — gate measurement and production-health adjudication are distinct, but the Spine gate was reconstructed rather than executed: `UNSCORABLE / GATE_NOT_EXECUTED`;
- historical healthy live sample — the shadow gate and later adjudication both rely on the same production-health measurement family: `UNSCORABLE / ADJUDICATION_REUSES_GATE_MEASUREMENT + GATE_NOT_EXECUTED`;
- current native-edition continuity — gate is derived and the repair adjudicator is Spine-derived: `UNSCORABLE / ADJUDICATION_NOT_INDEPENDENT_OF_SPINE + GATE_NOT_EXECUTED`.

Therefore sensitivity, specificity, false-block rate and false-allow rate remain `null` with zero scored episodes. This is a correction toward stricter evidence, not a regression in field capability.

## Executed local regression evidence

`tools/test_proof_spine_calibration_ledger_v4.py` passes **11/11** focused source-payload regressions in the local execution environment, including same-measurement specificity laundering, missing measurement provenance, executed-decision digest requirements, independent adjudication, zero-denominator honesty and episode deduplication.

This is local source-payload evidence only. The private Hub exact-head hosted workflow remains separately `UNEXECUTED` because that execution substrate has repeatedly failed before checkout; no exact-head PASS is claimed here.

## Next discriminator

The next useful specificity sample is not another Newsletter health rerun. It is a prospective episode where:

- an actually executed Spine gate says `OPEN`;
- a later project-owned mechanism with a **different measurement root** independently says `SHOULD_ALLOW` for the same subject;
- any consequential action/postcondition remains separately observable.

BLM is a strong candidate because D040 already provides a native queue referee for execution eligibility. A BLM adapter should wrap that local referee rather than copy its scheduling law into Spine. The later correctness adjudicator must be a distinct BLM-native postcondition/evidence mechanism, not the queue referee invoked twice.

## Promotion boundary

v0.3e does not promote Proof Spine, change FCMO canon, or grant action authority. It narrows what evidence is allowed to count toward calibration so future promotion cannot be won by correlated instrumentation.
