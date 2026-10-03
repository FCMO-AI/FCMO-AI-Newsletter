# Proof Spine shadow pilot — Newsletter evidence adapter

**Date:** 2026-09-14  
**State:** NON_NORMATIVE EXPERIMENT / NO PRODUCTION AUTHORITY

This branch tests one narrow integration boundary: can the Newsletter export enough **public-safe, project-native evidence** for a separate FCMO Proof Spine experiment to evaluate causal validity without copying private doctrine or changing publication behavior?

## Boundary

The Newsletter remains authoritative for its own publication state, health semantics, privacy boundary, localization contract, release gates, and live-site verification.

`tools/proof_spine_shadow_receipt.py` therefore does five bounded things:

1. executes the same Newsletter-local health commands already used by production health;
2. records their return codes, structured output when available, and a small set of source timestamps already present in public repository data;
3. proves whether the checkout's **material health inputs** still match one stable current `origin/main` before and after the observation window;
4. compares Newsletter's ingested public corpus with a **separately sanitized, currently sealable ARB public projection** without exposing private ARB state;
5. emits a JSON receipt with an explicit non-authority claim boundary.

It does **not** contain Proof Spine claims, gates, mission rules, publication authority, or action logic.

## Why source alignment is part of evidence

A branch can execute every local health check successfully while its Story data, status data, locale data, or checker semantics have drifted from current `main`. In that case, a green result is real execution evidence but not adequate evidence for the stronger claim “this describes current production.”

The receipt therefore exposes `source_alignment` separately from health:

- `MATCH` — all declared material health inputs match the same stable current-main SHA before and after the observation;
- `DRIFTED` — at least one material input differs;
- `CHANGED_DURING_OBSERVATION` — `main` changed during the observation window;
- `UNKNOWN` — current applicability could not be established.

Only `MATCH` allows the receipt summary to become `HEALTHY` or `UNHEALTHY`. Any other alignment state yields summary `UNKNOWN` while preserving the individual checker outputs as observations.

**Footnote for future maintainers:** `DRIFTED` does not mean the live website is broken. It means this checkout cannot truthfully certify the current-main health claim. Keep applicability failure separate from product failure.

Material alignment currently covers:

- `.github/workflows/newsroom-health.yml`;
- `site/data/newsroom-status.json`;
- `site/data/stories.json`;
- native `es-419` and `zh-Hans` data;
- editorial, translation, and live-newsroom verification tools;
- the real-browser autonomous-surface oracle.

## Why raw ARB commit movement is not freshness evidence

ARB is a private research/control-plane repository. Its `main` can advance because of candidates, question queues, research scans, or other private work that is **not yet public publication material**. Treating any private commit movement as “Newsletter stale” would manufacture false positives and would also pressure a public repo to learn private state it does not need.

The shadow witness instead asks the narrower public/public question:

> If current ARB `main` can be sealed into its approved sanitized public projection right now, does that public projection materially differ from the corpus Newsletter has actually ingested?

The workflow uses the same read-only GitHub App boundary as the real bridge, clones private ARB ephemerally, runs ARB's publication seal, copies only `_public_release`, then destroys the private checkout and seal log **before** Newsletter-side comparison or artifact creation.

The public adapter re-validates both sides with Newsletter's public-side bridge verifier and emits one of:

- `MATCH` — current sealable public projection and Newsletter corpus are identical;
- `MATERIAL_PUBLIC_DELTA_AVAILABLE` — public development identities changed and at least one changed identity has importance >=4;
- `NON_MATERIAL_PUBLIC_DELTA` — public bytes changed but no importance>=4 development identity changed;
- `UNKNOWN` — current ARB main could not be reduced to a sealed public projection or the comparison could not be established.

**Footnote for future maintainers:** `MATERIAL_PUBLIC_DELTA_AVAILABLE` is a synchronization fact, not automatically a claim that the currently served site is broken. Keep upstream material synchronization separate from serving, editorial, localization, and candidate-promotion truth unless Newsletter canon explicitly changes that causal contract later.

## Why this is federated instead of vendored

The Proof Spine engine currently lives as a private Agent Hub experiment. Copying it into this public repository would create two independently drifting engines and would expose private institutional implementation merely to run a pilot.

The intended experiment architecture is instead:

```text
Newsletter local checks + source applicability
                +
current sealable ARB public projection vs ingested public corpus
        ↓
public-safe shadow receipt
        ↓
Agent Hub experimental proof contract + engine
        ↓
shadow comparison only
```

That keeps local truth production near the project that owns it, while the experimental shared engine reasons over explicit receipts.

## Shadow-only behavior

The workflow has `contents: read` only. It can mint a read-only GitHub App token scoped solely to `AI-Research-Breakthroughs`, but it cannot publish, deploy, release, create issues, notify, or write repository state.

A local health check may be unhealthy, source applicability may be unknown, the branch may be drifted, or an upstream material delta may exist and the exporter can still complete successfully: the purpose of the workflow is to **observe and preserve evidence**, not to become a hidden replacement gate.

While this experiment remains an unmerged PR, push/manual triggers are the executable validation surface. The workflow also declares future `workflow_run` triggers for:

- `Autonomous newsroom production health` completion;
- `Pull airlocked newswire with GitHub App` completion.

GitHub resolves `workflow_run` from the default branch, so those triggers remain dormant until the workflow is actually accepted into `main`. If accepted, this makes the witness event-driven after the existing production-health/transport cycles instead of adding another blind polling schedule.

Artifacts are retained for 90 days so a naturally occurring sensitivity event is less likely to disappear before it can be correlated with production history.

## Prospective evidence already obtained

The first producer run proved that the adapter and all five local checks could execute prospectively, but its receipt predated source-alignment attestation and is therefore not grandfathered as current-health proof.

The hardened second run, `34911725577`, on branch head `7d3e8da10425e644696f94131a35eefde167588b`, produced an aligned receipt with:

- `source_alignment.before = MATCH`;
- `source_alignment.after = MATCH`;
- the same observed current-main SHA `befabad866e95c1258db1d8edce92ea308291853` at both boundaries;
- no drifted material paths;
- all five project-native health checks `EXECUTED/PASS`;
- local state/quality `HEALTHY / HEALTHY`.

That is specificity evidence for the **public evidence boundary**. It does not prove the private Agent Hub consumer, grant publication authority, or establish unique Proof Spine value.

## Upstream synchronization witness — exact baseline

The first complete sanitized upstream witness ran successfully in run `34913181810`. The final event-driven-capable workflow head then re-ran the whole path in run **`34913420949`** on head `4dca67eb9eb1517b694b2c06fa6bd65b7dd94fee`.

Every workflow step completed `success`, including:

- read-only GitHub App token minting;
- reduction of current private ARB main to a sanitized publication witness;
- private checkout/log destruction before comparison;
- adapter compilation;
- all five Newsletter-native health observations;
- public/public synchronization comparison;
- non-enforcing Actions summary;
- artifact upload.

Run `34913420949` produced artifact `10375183162`:

- ZIP SHA-256 `8b3b3daae20e056430376cef1c02a2cb5b14b425f4c1a1aed7be203d069facdc`;
- receipt JSON SHA-256 `888cd02f9258e6460513f4ab944fb5bfb8f85e200162d9cb9d204ef103c3bc70`;
- receipt observed `2026-09-15T00:30:48.005618Z`;
- retention through `2026-12-14`.

The result was deliberately **not** the sensitivity win the experiment is waiting for:

```text
Newsletter local state       = HEALTHY / HEALTHY
Newsletter source alignment  = MATCH
current sealable ARB public   = MATCH
Newsletter ingested corpus    = MATCH
material public delta IDs     = []
```

Both public corpus digests were exactly:

`a292b96bc8b127299499c1be873fc218d216d91d1b9de064da5ca533a0a45204`

Both represented 42 records and release id `newswire-a292b96bc8b127299499c1be`.

This is useful **specificity** evidence for the new upstream witness: private ARB commit churn did not become a fabricated Newsletter freshness incident. It is explicitly **not sensitivity evidence**.

The existing Newsletter release validator also passed against the same functional head in run `34913423343`.

## Success criterion

This pilot is useful only if the external Proof Spine evaluation can compare its decision against the Newsletter's existing local decision surface while preserving important distinctions such as:

- candidate proof vs currently served known-good health;
- evidence execution vs applicability to current `main`;
- local health vs upstream material synchronization;
- private ARB work vs actually sealable public publication material;
- `HEALTHY` vs `DEGRADED_ACCEPTABLE` vs `UNHEALTHY` vs `UNKNOWN`;
- periodic observations vs exact deterministic freshness deadlines;
- local checker evidence vs shared proof-contract semantics.

Agreement on aligned healthy/synchronized samples is specificity evidence, not proof of unique value. Promotion still requires a **natural prospective sensitivity sample** where Proof Spine catches a consequential stale/invalid/unknown dependency that the existing local system would otherwise leave live or materially ambiguous, without unacceptable false blocks or maintenance burden.

Do not inject an artificial production failure merely to manufacture that sample.
