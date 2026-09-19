# FCMO Proof Spine v0.2b — Newsletter upstream material-sync witness

**Date:** 2026-09-14  
**Authority:** NON_NORMATIVE EXPERIMENT  
**State:** REAL PUBLIC-SAFE WITNESS EXECUTED; sensitivity not yet observed

## Problem exposed by the field pilot

Newsletter's existing hourly health surface can establish serving, live autonomous surfaces, Airlock age, editorial freshness, localization health, and current-main applicability.

That is not the same question as:

> **Has Newsletter ingested the latest material publication state that ARB could safely publish right now?**

The Newsletter product goal explicitly cares about upstream public-safe freshness. But a raw ARB commit comparison would be wrong: private ARB `main` legitimately moves for candidates, question queues, scans, and other research/control-plane work that is not public publication material.

The non-dominated witness is therefore a **sanitized public→public comparison**, not private-head chasing.

## Public-safe witness architecture

```text
private ARB current main
        ↓ publication_seal.py inside ephemeral private checkout
sanitized _public_release only
        ↓ destroy private checkout + seal log
Newsletter public-side release verifier
        ↓
current sealable public corpus digest + public development identities
        ↕ compare
Newsletter ingested corpus digest + public development identities
        ↓
MATCH | MATERIAL_PUBLIC_DELTA_AVAILABLE | NON_MATERIAL_PUBLIC_DELTA | UNKNOWN
```

The Newsletter workflow uses the same GitHub App identity class as the real bridge, read-only and repository-scoped to private ARB. No private source SHA, candidate record, research link, seal log, or private checkout enters the public receipt.

If current ARB main cannot seal, the witness returns `UNKNOWN`. It does **not** fall back to an older ready snapshot because its narrow question is current sealability, not “find anything publishable.” It also does not declare production unhealthy merely because current main is temporarily unsealable.

## Materiality boundary

Digest inequality alone is not treated as a consequential incident.

The witness compares public `data/developments.jsonl` rows by stable public id and canonical row digest. It classifies the public delta as material only if at least one added/removed/changed public development has effective importance >=4.

States:

- `MATCH` — public corpus digests match exactly;
- `MATERIAL_PUBLIC_DELTA_AVAILABLE` — a public development identity changed and at least one changed identity is material;
- `NON_MATERIAL_PUBLIC_DELTA` — public bytes differ without a material development identity change;
- `UNKNOWN` — current public projection or comparison cannot be established.

This deliberately resists both false persistence and false sensitivity.

## Causal isolation inside Proof Spine

The private v0.2b contract adds evidence:

`live_upstream_material_sync`

and the independent branch:

```text
live_upstream_material_sync
        ↓
live_upstream_material_synced
        ↓
represent_live_upstream_material_synced
```

It is **not** inserted into `current_live_production_healthy`.

That choice is intentional. A newly sealable material ARB delta can prove that Newsletter's ingested corpus is behind without proving that:

- the currently served site is unreachable;
- the current Story set has crossed its hard freshness boundary;
- localization is broken;
- the candidate transaction was deployed;
- the existing live edition became corrupt.

A future sensitivity sample should therefore close only the synchronization claim unless the independent local health evidence also changes.

## Adversarial regression surface

The Newsletter shadow suite now adds three discriminating cases on top of the earlier eight:

9. `MATERIAL_PUBLIC_DELTA_AVAILABLE` closes only the upstream-sync gate while current live-health remains OPEN;
10. a non-material byte/public-row delta does not manufacture material lag;
11. an unsealable current ARB main produces upstream `UNKNOWN` without poisoning established live-health evidence.

These tests are present on the current Hub branch. The private exact-head runner remains unavailable in the current environment, so do not represent them as exact-head executed yet.

## Exact prospective baseline — sample #3

The first successful upstream witness run was `34913181810`.

The final event-driven-capable Newsletter workflow head `4dca67eb9eb1517b694b2c06fa6bd65b7dd94fee` then executed run **`34913420949`**. Every step completed successfully, including private→public reduction, private-state destruction, receipt production, summary, and upload.

Artifact `10375183162`:

- ZIP SHA-256: `8b3b3daae20e056430376cef1c02a2cb5b14b425f4c1a1aed7be203d069facdc`;
- receipt JSON SHA-256: `888cd02f9258e6460513f4ab944fb5bfb8f85e200162d9cb9d204ef103c3bc70`;
- receipt bytes: `7901`;
- observed: `2026-09-15T00:30:48.005618Z`;
- artifact retained through `2026-12-14`.

Observed state:

```text
Newsletter local health      HEALTHY / HEALTHY
source alignment             MATCH
current sealable ARB public  MATCH
Newsletter corpus            MATCH
material public delta        []
```

Exact public corpus identity on both sides:

- digest `a292b96bc8b127299499c1be873fc218d216d91d1b9de064da5ca533a0a45204`;
- 42 records;
- release id `newswire-a292b96bc8b127299499c1be`.

This is a **negative sensitivity result but positive specificity result**: the witness had a chance to accuse the pipeline and correctly did not. Private ARB movement did not become a fabricated public-freshness incident.

The exact lineage is preserved in `2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_PROSPECTIVE_SHADOW_SAMPLE_003_v0.2b.json`.

## Event-driven observation path

The Newsletter workflow now declares `workflow_run` triggers after:

- `Autonomous newsroom production health` completion;
- `Pull airlocked newswire with GitHub App` completion.

GitHub resolves `workflow_run` from the default branch, so these are intentionally dormant while PR #43 remains unmerged. If that evidence adapter is separately accepted into Newsletter `main`, the witness will run after existing production-health/transport events rather than adding another blind timer.

The workflow still has no production write authority. A material-lag result is evidence, not an automatic deploy, publish, rollback, issue, or release action. Artifacts are retained 90 days to give a naturally occurring sensitivity sample a durable observation window.

## Promotion boundary

Proof Spine **still has not earned promotion** from this sample.

The missing evidence remains exactly the hard part:

> prospectively catch a consequential stale/invalid/unknown dependency that existing local machinery would otherwise leave live or materially ambiguous, while preserving unrelated valid truths and avoiding unacceptable false blocks/maintenance burden.

Do not inject an artificial production fault to manufacture this result. The correct next sample is one produced by actual pipeline evolution, source drift, freshness expiry, or another naturally occurring dependency failure.
