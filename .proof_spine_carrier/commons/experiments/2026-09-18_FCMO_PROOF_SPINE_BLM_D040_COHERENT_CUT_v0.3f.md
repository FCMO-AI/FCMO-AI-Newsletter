# FCMO Proof Spine — BLM D040 coherent-cut falsification v0.3f

**Date:** 2026-09-18  
**State:** NON_NORMATIVE FIELD EVIDENCE  
**Project authority:** BLM remains authoritative for BLM scheduling/science.

## What was falsified

The v0.3e BLM producer correctly proved one proposition: the canonical queue was structurally accepted by `tools/continuous_science_referee.py`.

It did **not** prove the stronger proposition encoded by the shadow gate: that the declared H12 primary was still a current action worth admitting.

Before Spine's v0.3e observation at `2026-09-18T04:35:39.135929Z`, BLM had already committed `99b78ba2118cb898d81fd45e908815b8f3dc66e5` at `2026-09-17T23:16:28Z`. Its project-local receipt `research/QUEUE_RECONCILIATION_REQUIRED_2026-09-18.json` explicitly says the H12 action in the older queue was consumed/superseded and must not be re-executed before reconciliation.

Thus the old structural OPEN is preserved as a real false-allow-shaped field falsification: the checker was truthful about structure but the proof graph omitted a live invalidator.

## Corrected project-side execution

BLM PR #23 head `3a0f61fb9721fbf9b08f02746076eecbd489b2f4` re-ran on HUAWEI as run `35309072696`.

Observed steps:

- exact candidate checkout: PASS;
- BLM structural D040 referee: PASS;
- corrected adapter regressions: **8/8 PASS**;
- exporter: expected nonzero because coherent cut says DENY;
- receipt artifact preservation: PASS.

Artifact `10532329395`:

- ZIP SHA-256: `a7cbb132d7012bfc4d891b95e3e80e411c65069b5bd21bc3304f56c4001b9f3b`;
- exact JSON bytes: `3806`;
- exact JSON SHA-256: `012a275137203dfed6d080f436b6b7c46cdaf1ea92984aebe9e3389fad407c36`;
- canonical Proof Spine project-receipt digest: `3331ceb3464f1553f9dd1e324885d0d10d4538bcef59f0fa2b56017adc9cc2bd`.

The receipt contains two independent primitives:

1. `d040_queue_execution_contract_valid = PASS`;
2. `d040_primary_reconciliation_clear = FAIL`.

BLM's own local decision is therefore `scheduler_may_execute_primary = DENY`.

## Universal correction

v0.3f introduces reviewed `decision_cuts` in the universal project/federation integration layer.

A mutable action gate may declare the exact evidence surfaces that constitute its coherent decision lease. The integration layer then rejects the contract if:

- a required surface is absent from runtime evidence;
- a required surface is merely documented but does not transitively feed the gate;
- a mutable required surface lacks reviewed freshness, unless the contract explicitly marks that surface stable.

The mechanism is domain-neutral. BLM defines that queue structure and reconciliation state belong in this particular cut. Another FCMO project may declare entirely different invalidators.

> **OPEN is a lease on coherent current decision state, not a permanent reward for one green checker.**

## Calibration boundary

This event is negative field evidence, but the old private Hub gate was reconstructed rather than prospectively executed by a runnable Hub substrate. Under v0.3e/v0.3f calibration rigor it therefore remains **UNSCORABLE** for headline sensitivity/specificity rates.

Its decision relation is nevertheless clear and preserved: old shadow decision `OPEN`, later independent project-local adjudication `SHOULD_BLOCK`, disjoint measurement roots. The rate denominator stays honest instead of laundering a reconstructed gate into statistics.

No BLM action, merge, experiment launch, compute allocation, scientific promotion, or canonical scheduling mutation is authorized by this note.
