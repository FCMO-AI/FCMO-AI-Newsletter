# FCMO Proof Spine v0.3d — calibration provenance correction

**Date:** 2026-09-17  
**Authority:** NON_NORMATIVE EXPERIMENT  
**State:** CALIBRATION DENOMINATORS RESET PENDING EXECUTED DECISION RECEIPTS

## The defect

v0.3c correctly required later project-local adjudication to be independent of Spine, but it still accepted a gate label/timestamp without proving that Proof Spine had actually emitted that decision.

That means a deterministic derivation or later reconstruction could improve sensitivity/specificity as if it were runtime evidence.

For a proof system, that is circularly weak.

## v0.3d law

A calibration event is scoreable only when **both** sides are independently grounded:

1. the later truth label comes from project-local adjudication independent of Spine; and
2. the earlier Spine decision has `EXECUTED` provenance bound to:
   - exact proofspec SHA-256;
   - exact effective-evidence SHA-256;
   - exact `FCMO_PROOF_SPINE_DECISION_RECEIPT` SHA-256;
   - exact evaluation timestamp and evidence references.

`DERIVED` and `RECONSTRUCTED` decisions stay valuable for field investigation, architecture, and falsification, but do not enter accuracy denominators.

## What this does to current evidence

The reset is intentionally severe:

- the natural pre-action localization catch remains a strong temporal/field result, but its Hub gate was reconstructed from the exact public receipt rather than emitted as an exact-head decision receipt → **UNSCORABLE**;
- the first aligned healthy sample has a later independent all-green Newsletter health run on the same `befabad…` main SHA, so it is a real positive specificity opportunity, but its Spine gate was explicitly recorded as `DERIVED_NOT_EXACT_HEAD_EXECUTED` → **UNSCORABLE**;
- the current `29cf44c…` continuity case is both gate-derived and later validated by the Spine-derived repair PR #44 → **UNSCORABLE** for two independent reasons.

Therefore the v0.3d field report truthfully returns:

- executed gate cases: **0**;
- scored episodes: **0**;
- sensitivity: **null**;
- specificity: **null**;
- false-block rate: **null**;
- false-allow rate: **null**.

This supersedes v0.3c **for promotion/calibration claims only**. v0.3b/v0.3c remain preserved as lineage showing why the stricter requirement was discovered.

## New positive field fact preserved without gaming

Newsletter shadow sample #2 at `2026-09-15T00:11:03.258046Z` represented `befabad866e95c1258db1d8edce92ea308291853` with source alignment `MATCH` and derived live-health gate `OPEN / VALID`.

A later independent project-local health run, `34914298913`, ran on the same main SHA at `2026-09-15T00:42:41Z` and completed all four jobs successfully:

- serving-health;
- publication-freshness;
- editorial-freshness;
- translation-health.

That is precisely the kind of case that should populate specificity once the earlier gate is an executed, byte-addressed decision receipt. v0.3d preserves it but refuses to score it early.

## Regression surface

`tools/test_proof_spine_calibration_ledger_v3.py` proves:

- executed + independently adjudicated decisions can score;
- DERIVED and RECONSTRUCTED gates cannot score;
- non-executed gates cannot smuggle decision hashes;
- executed gates require proofspec/effective-evidence/decision-receipt hashes;
- fake digests and mismatched evaluation timestamps fail closed;
- independent adjudication remains separately mandatory;
- zero executed cases preserve null rates;
- a genuinely executed true-allow creates a specificity denominator;
- episode deduplication remains intact.

## Next discriminating evidence

The next valuable step is **not another reconstructed case**.

Proof Spine needs a universal decision-receipt path that executes the actual reviewed contract over exact evidence and emits a byte-addressed `FCMO_PROOF_SPINE_DECISION_RECEIPT`. Once such receipts exist prospectively, current natural negative and positive project-local adjudications can finally calibrate sensitivity and specificity honestly.
