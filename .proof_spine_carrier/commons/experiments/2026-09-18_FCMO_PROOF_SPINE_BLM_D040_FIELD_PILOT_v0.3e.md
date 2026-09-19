# FCMO Proof Spine — BLM D040 field pilot v0.3e

**Date:** 2026-09-18  
**State:** NON_NORMATIVE FIELD EVIDENCE  
**Project authority:** BLM remains authoritative for BLM scheduling and science.

## Exact project-side execution

BLM draft PR #23 (experiment/proof-spine-d040-queue-shadow-v0.1) executed on the HUAWEI self-hosted runner.

Corrected exact-head run: 35307514190 on head f97ebfdc5806c15ca968eb4f74a2c6a5d52db081.

The first run was intentionally not accepted as exact-head provenance because pull-request checkout used GitHub's synthetic merge ref. The workflow was corrected to checkout pull_request.head.sha, then re-executed.

Observed evidence:

- BLM-native tools/continuous_science_referee.py: PASS;
- referee summary: items=9 executable=2 primary=H12_LATE_TASK_ELASTIC_FUTURE_INTERFACE backup=H16_SUCCESSOR_BINDING_COMPETENCE_ROUTE;
- adapter regressions: **5/5 PASS**;
- exporter: PASS;
- artifact id: 10532745399;
- artifact ZIP SHA-256: e42ae79f906d698e9c820bf76ab71a42bbf3642d8c55d6bc4f058c731988b786;
- exact JSON bytes: 2238;
- exact JSON SHA-256: d25e649d6c51ffa8774ee51ab166e9f93b13754a8323c4625dfead534263de10;
- Proof Spine canonical receipt digest: 83aaead2d80060383646005c5ccf2208fc54ef20548dd808645779e47c71ca05.

The receipt reports PASS for d040_queue_execution_contract_valid and preserves BLM's local scheduler_may_execute_primary=ALLOW decision. The receipt explicitly carries SCHEDULING_STRUCTURE_ONLY_NO_SCIENTIFIC_PROMOTION_NO_COMPUTE_LAUNCH.

## Universal consumer boundary

The paired Hub proof contract consumes only that one BLM-local scheduling premise and exposes one shadow gate: shadow_admit_blm_primary_execution.

An OPEN result means only that BLM's own current D040 scheduling structure admits the declared primary. It is not scientific correctness, architecture/model promotion, representative-scale evidence, resource authorization, or experiment success.

## Why this is not specificity yet

This pilot creates a real prospective **OPEN observation path** in a second FCMO domain. Under calibration v0.3e, it cannot become TRUE_ALLOW by rerunning the D040 referee. A scoreable specificity episode requires:

1. an actually executed, byte-addressed Spine OPEN decision;
2. later BLM-local adjudication bound to the same subject;
3. that adjudicator must be independent of Spine;
4. its measurement root must be disjoint from the D040 queue referee.

The next valid adjudicator should therefore be an experiment/evidence postcondition appropriate to the exact H12 unit if/when that unit is consumed—not another scheduler check.

## Promotion boundary

BLM #23 and Hub #55 remain draft/unmerged. This is portability and observation evidence, not promotion authority.
