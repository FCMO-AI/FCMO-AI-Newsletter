# FCMO Proof Spine v0.3 — Universal Federation Architecture

**Date:** 2026-09-15  
**State:** NON_NORMATIVE EXPERIMENT  
**Authority:** no promotion/release authority; project-local law remains authoritative for project truth and action  

## Correction

The v0.2 field campaign over-focused on Newsletter because Newsletter was the first project with a mature, observable live pipeline and therefore a useful proof target. That was useful experimental pressure, but it risked making the implementation *look* like an observability subsystem for one product.

That is the wrong product boundary.

> **Proof Spine is an FCMO-wide validity fabric. Newsletter is one adapter and one field pilot.**

The universal object is not “Newsletter health.” It is the relationship:

```text
PROJECT-OWNED EVIDENCE
        ↓
UNIVERSAL EVIDENCE-ONLY RECEIPT
        ↓
REVIEWED PROOF CONTRACT
        ↓
GENERIC DEPENDENCY ENGINE
        ↓
VALID / INVALID / STALE / UNKNOWN
        ↓
PROJECT OR CROSS-PROJECT GATES
```

The generic engine must not know what a newspaper, compression ratio, GPU, model checkpoint, deployment, benchmark, procurement record, game build, or memory fabric is.

## Five-layer architecture

### 1. Proof Spine Core

`tools/proof_spine_v2.py` remains the domain-neutral causal evaluator:

- separate proof contract and runtime evidence;
- `VALID / INVALID / STALE / UNKNOWN`;
- `all / any / at_least`;
- causal-root independence;
- fail-closed gates;
- blast radius;
- minimal repair frontier;
- temporal invalidation;
- counterfactual simulation;
- coverage lint.

The core receives evidence and a contract. It does not discover project truth and does not execute external actions.

### 2. Universal Project Receipt

`tools/proof_spine_federation.py` introduces one shared integration boundary:

`FCMO_PROOF_SPINE_PROJECT_RECEIPT`

Every participating project may produce the same top-level shape:

```json
{
  "schema_version": 1,
  "kind": "FCMO_PROOF_SPINE_PROJECT_RECEIPT",
  "authority": "EVIDENCE_ONLY",
  "project": {
    "id": "project-id",
    "repository": "owner/repo"
  },
  "observed_at": "...",
  "scope": {},
  "evidence": [],
  "local_decisions": [],
  "claim_boundary": "..."
}
```

The exact experimental schema is preserved at:

`commons/experiments/2026-09-15_FCMO_PROOF_SPINE_PROJECT_RECEIPT_SCHEMA_v0.3.json`

A receipt may carry rich local metadata, but it may not carry `mission`, `claims`, or `gates`. Evidence producers do not get to author the acceptance contract that judges them.

### Contract-closed identity: receipts report identity; contracts decide membership

A universal evidence format is unsafe if presenting a syntactically valid receipt is enough to enter a proof graph. Runtime evidence must not self-enroll the project whose gates it can influence.

v0.3 therefore closes identity in both modes:

- **project mode:** `mission.context` must independently bind at least `project_id` and `repository`; any additional reviewed scope keys must also match the receipt;
- **federation mode:** `federation.receipt_requirements` must be a non-empty exact membership set, and every member must bind `project_id → repository` in the proof contract;
- required-but-missing members fail configuration closed;
- extra runtime members not declared by the contract are rejected;
- the same repository cannot appear as two federation members, including casing aliases such as `FCMO-AI/Repo` vs `fcmo-ai/repo`;
- local evidence IDs may not claim the `::` federation namespace.

Repository identity is currently represented as reviewed GitHub `owner/repository` text and compared case-insensitively. A stable repository-ID binding is a plausible later hardening if repository rename/transfer behavior becomes decision-relevant; it is not silently claimed here.

> **A receipt may say who it is. Only the reviewed contract may decide that this is the identity it intended to judge.**

This closes the same authority gap on both sides of the universal layer: producers cannot self-author either **acceptance law** or **membership**.

### Temporal authority: observation belongs to the producer; accepted lifetime belongs to the contract

A universal validity fabric cannot let an evidence producer keep its own `PASS` alive indefinitely by omitting a TTL or selecting a generous one. v0.3 therefore separates two authorities:

- **producer authority:** what was observed, its timestamp, local status, provenance and any stricter local expiry;
- **proof-contract authority:** how long that observation is acceptable for the particular represented claim/gate.

The reviewed proofspec may declare:

- project/federation `freshness_requirements[evidence_id].max_age_hours`;
- `federation.receipt_requirements[project].max_receipt_age_hours`.

The effective lifetime is the strictest applicable bound. Producer `max_age_hours` may **tighten** a reviewed maximum but may not widen it.

If reviewed freshness requires an evidence observation timestamp and the producer omitted it, an otherwise positive status becomes `UNKNOWN`; regenerating a fresh receipt is not allowed to masquerade as refreshing the underlying observation.

Temporal provenance is also internally ordered: an individual evidence observation may not claim `observed_at` later than the enclosing project receipt's `observed_at`. A future-dated project receipt is rejected at evaluation time. The generic temporal invalidator remains defense-in-depth for engine-shaped envelopes, but the universal validated receipt path rejects impossible observation chronology before it reaches ordinary state propagation.

This gives Spine an explicit anti-zombie law:

> **A new envelope is not new evidence. Time freshness attaches to the observation whose truth is being reused, under a lifetime chosen by the reviewed contract.**

### Evidence identity remains independent from the judge

Contract-owned TTLs and reviewed causal equivalence intentionally transform the effective envelope that the generic engine evaluates. Those transformations must not retroactively change the identity hash of the evidence that was supplied.

The federation therefore exposes two distinct digests:

- `federated_evidence_digest` — digest of the raw, namespaced evidence envelope **before** proof-contract TTL/common-cause transformation;
- `effective_evidence_digest` — digest of the exact transformed envelope evaluated by the engine.

Per-project `project_receipt_digest` likewise remains a digest of the producer-owned receipt.

**Footnote:** changing a proof contract should change `proofspec_digest` and may change `effective_evidence_digest`; it must not make identical supplied evidence appear to be different source evidence. This preserves the architectural boundary `proof contract != runtime evidence` even after federation policy is applied.

### 3. Project Adapters

Adapters stay thin and local to project semantics.

Examples:

- Newsletter maps serving/browser/Airlock/editorial/localization/upstream-publication observations;
- CMPCT can map benchmark semantics, deterministic archive-size parity, timing parity, portability, format/conformance and release evidence;
- BLM can map scientific-integrity, matched-control, scale/MRS regime, Q4-like behavior, compute/data provenance and experiment evidence;
- Hermes could map memory-fabric checkpoint/continuity/provenance/recovery evidence;
- NOVA could map build/test/content-integrity/gameplay-regression evidence;
- VIVO could map host/VM/node capability and system-integration evidence.

Those examples describe integration *shape*, not current adoption claims. A project is not “on Spine” merely because an example exists here.

**Footnote:** local adapters are allowed to be custom code. Universal architecture does not mean forcing every repository into one brittle declarative mapper. The invariant is the receipt boundary, not one implementation language.

### 4. Project Proof Contracts

A project or Hub experiment may define a reviewed proofspec whose claims/gates express the real dependency graph for that mission.

Project contracts remain separate because FCMO repositories have materially different laws. CMPCT release promotion must not be rewritten as BLM model-science promotion; BLM MRS/Q4 rules must not be rewritten as Newsletter freshness semantics.

Universal Spine standardizes **how evidence and causal validity compose**, not what each project's truth conditions should be.

A project-mode contract must also bind the project identity it is intended to judge. Generic reusable templates are acceptable as authoring aids, but they must be instantiated into a project-bound proofspec before evaluation.

### 5. Federation

Multiple project receipts can be evaluated together without becoming one monolithic global health flag.

The federation layer namespaces evidence as:

`project_id::local_evidence_id`

This prevents accidental name collision such as two repositories both exporting `health`.

Local causal roots are also isolated by default:

`project_id::local_causal_root`

Federation membership itself is contract-closed through `federation.receipt_requirements`; runtime receipts cannot add an undeclared project merely by presenting a valid envelope.

Cross-project common-cause equivalence is **not** producer-controlled. When two project observations genuinely descend from one real upstream cause, the reviewed proofspec may declare that relationship under:

```json
{
  "federation": {
    "receipt_requirements": {
      "project-a": {"repository": "owner/project-a"},
      "project-b": {"repository": "owner/project-b"}
    },
    "causal_equivalence": [
      {
        "id": "one-real-upstream",
        "members": ["project-a::evidence", "project-b::evidence"]
      }
    ]
  }
}
```

The federation layer then gives those members one shared causal root before the generic engine evaluates `at_least.independent`.

**Footnote:** this is deliberately contract-side rather than receipt-side. Common-cause equivalence changes whether evidence counts as independent corroboration, so a runtime producer must not be able to self-award independence or correlation by attaching metadata to its own evidence. The relationship belongs in the reviewed proof contract and therefore inside the proofspec digest.

## Universal does not mean global contagion

The most important federation rule is negative:

> **FCMO-wide availability of Spine does not create an FCMO-wide health gate.**

A CMPCT archive-size regression should close CMPCT's represented release gate. It should not make BLM experiments invalid or Newsletter unhealthy.

A BLM experiment whose Minimum Representative Scale remains unknown should remain unpromoted/unknown at that proof surface. It should not poison a valid CMPCT release receipt.

A Newsletter upstream-material lag should not invalidate unrelated serving or localization truths, much less unrelated repositories.

Cross-project claims are legitimate only when the proof contract names a real causal dependency. Examples could include a shared release artifact, shared compute substrate, a project consuming another project's output, or an FCMO operational decision that truly requires several independent project proofs.

No dependency by proximity, branding, repo ownership, or narrative association.

## Executable cross-domain discriminator

The v0.3 regression suite deliberately uses three materially different FCMO domains under one engine:

1. **Newsletter** — material publication synchronization;
2. **CMPCT** — release-parity evidence modeled from current CMPCT local law: benchmark-semantic equivalence, zero-byte archive-size regression tolerance, same-runner timing parity and portability;
3. **BLM** — scientific-promotion evidence modeled from current BLM local law: scientific integrity, matched control, scale/MRS regime and Q4-like behavior.

These fixtures are **synthetic regression fixtures**, not claims about current project state.

The point is architectural falsification: the shared integration/core must work without domain branches.

The suite requires:

- all three distinct project gates can open through the same engine;
- a CMPCT size regression closes only CMPCT's gate;
- a BLM unknown scale regime closes only BLM's gate as `UNKNOWN`;
- identical local evidence IDs are safely namespaced;
- identical local causal-root labels do not accidentally correlate projects;
- reviewed proof-contract causal equivalence prevents two derivative project observations from being counted as two independent confirmations;
- runtime evidence cannot self-declare shared causal equivalence;
- a project receipt cannot smuggle its own claims/gates into the evaluator;
- project-scope metadata cannot override project identity;
- local evidence IDs cannot impersonate the federation namespace;
- project-mode proof contracts must bind `project_id` and `repository`;
- federation membership must exactly match the reviewed member set;
- every federation member must have a reviewed repository binding;
- repository casing aliases cannot manufacture two independent members;
- project-scope mismatch is rejected before evidence enters federation;
- an evidence observation later than its enclosing receipt is rejected as impossible provenance;
- reviewed freshness can stale evidence even if the producer omitted its own TTL;
- a producer cannot widen reviewed freshness but may tighten it;
- regenerating a receipt cannot rejuvenate an old underlying observation;
- future project receipts are rejected;
- changing proof-contract freshness leaves raw evidence identity unchanged while changing the effective evaluated envelope where appropriate.

The corresponding proofspec is:

`commons/experiments/2026-09-15_FCMO_PROOF_SPINE_UNIVERSAL_MULTI_PROJECT_PROOFSPEC_v0.3.json`

The executable suites are:

- `tools/test_proof_spine_federation.py`
- `tools/test_proof_spine_temporal_integrity.py`

## Newsletter demotion from “center” to “adapter”

`tools/proof_spine_newsletter_shadow.py` now converts the project-local Newsletter receipt into the same universal `FCMO_PROOF_SPINE_PROJECT_RECEIPT` used by the federation layer, then evaluates through `proof_spine_federation.evaluate_project(...)`.

Newsletter-specific semantics remain useful and preserved, but they no longer define a special engine path. Its project proofspec now explicitly binds `project_id = newsletter` and repository `FCMO-AI/FCMO-AI-Newsletter`, so the same contract cannot silently evaluate a different receipt merely because that receipt exports similarly named evidence.

This is the migration pattern for every other project:

```text
local truth machinery
    ↓ thin adapter
FCMO_PROOF_SPINE_PROJECT_RECEIPT
    ↓
shared project/federation layer
    ↓
shared Proof Spine core
```

## Second real pilot: CMPCT, not another synthetic example

CMPCT now supplies the first real non-Newsletter discriminator through draft PR `FCMO-AI/.CMPCT#110`, based on its active `agent/v030-authoritative-integration` frontier rather than stale `main` state.

Successful hosted run `35034489645` executed the adapter on GitHub's merge checkout, passed 8/8 adapter regressions, directly exported the evidence-only receipt, verified that the receipt contained no proof-contract authority, and uploaded artifact `10422996630`.

The observed CMPCT strict lock remained `LOCKED` with `0/12` required release receipts accepted. Spine did not reinterpret that into release permission or fake product failure; the adapter exported missing promotion proof conservatively as `UNKNOWN`.

Immutable field details and claim boundaries are recorded in:

`commons/experiments/2026-09-15_FCMO_PROOF_SPINE_CMPCT_FIELD_PILOT_v0.3.md`

This closes the **portability** question “can a materially different real FCMO project export its existing local truth machinery through the universal receipt without surrendering authority?” for one non-Newsletter project. It does not close the harder **sensitivity** question “does Spine catch a consequential validity failure local machinery would otherwise leave live or materially ambiguous?”

## Authority topology

Proof Spine federation is deliberately weaker than project authority.

- **Project repository** owns current project truth, local evidence semantics, release/science/product law, and local action authority.
- **Project adapter** owns translation from local observations into evidence-only receipt semantics.
- **Proof contract** owns the reviewed subject identity/membership, dependency graph, accepted evidence/receipt freshness ceilings, any cross-project causal equivalence, and represented gates for that particular mission.
- **Proof Spine core** owns deterministic propagation under the supplied contract/evidence.
- **Agent Hub** may host shared engine/schema/experiments and cross-project contracts, but does not become the source of volatile project state merely because federation exists.
- **Promotion authority** remains separate.

This follows the Hub's existing rule: universal canon connects the ecosystem; project canon specializes it.

## What universal adoption would eventually require

A future FCMO-wide promotion should not mean copying a workflow into every repository. The minimum useful adoption contract is smaller:

1. a participating project can emit or be adapted into an `EVIDENCE_ONLY` project receipt;
2. the receipt binds observation to project/scope/provenance strongly enough for its claims;
3. a reviewed project proofspec binds the project identity it intends to judge, and a federation contract explicitly binds every member/repository it admits;
4. a reviewed proofspec exists for any gate Spine is expected to represent;
5. accepted freshness lifetime is contract-owned rather than producer-self-awarded;
6. raw evidence identity stays independently digestible from proof-contract transformations;
7. project-local authority remains explicit;
8. cross-project composition is namespaced and causal, not organizationally contagious;
9. real project pilots show useful sensitivity without unacceptable false blocks or maintenance burden.

Projects that do not benefit from Spine should not be forced to produce ceremonial receipts.

## Deliberately parked structural frontier: multiple surfaces from one repository

The current federation deliberately accepts one receipt per `project.id` and one represented repository per federation evaluation. That prevents one repository from masquerading under multiple aliases to fake independence.

A mature FCMO system may eventually need more than one simultaneously independent proof surface from one repository—for example candidate-release truth and currently-served production truth, or scientific-result truth and compute-substrate truth. Supporting that safely requires an explicit reviewed **surface identity** model that cannot be abused to manufacture causal independence.

This is **parked, not ignored**. Current Newsletter and CMPCT pilots can truthfully aggregate the necessary local surfaces into one project receipt, so inventing a multi-receipt identity layer now would add complexity without decision-changing field evidence. Reopen when a real project requires concurrent separately scoped receipts that cannot be represented cleanly inside one envelope.

## Remaining proof debt

This BONK materially improves the universal architecture, but it does **not** promote v0.3 to FCMO canon.

Remaining debt includes:

- exact-head execution of the private Hub generic + federation + temporal-integrity + adapter suites; three hosted attempts across PR and branch-push event paths have failed before any job step began, so this remains `UNEXECUTED`, not code `FAIL` or `PASS`;
- prospective sensitivity evidence where Spine catches a consequential validity break current local machinery would otherwise leave ambiguous/live;
- maintenance-cost and false-block evidence showing that project adapters/contracts remain thin enough to justify the shared layer;
- field pressure on the parked multi-surface identity question if/when a real project needs it;
- possible stable repository-ID binding if rename/transfer identity becomes a real threat rather than a hypothetical one;
- eventual Governance/promotion decision if the capability earns canonical status.

The prior debt item “at least one non-Newsletter real project adapter/pilot” is now satisfied by the CMPCT field pilot and should not be carried forward as if only synthetic fixtures existed.

Until the remaining debt is closed, the truthful statement is:

> **Proof Spine is now architected and implemented as a universal FCMO validity-federation experiment with contract-closed identity/membership, contract-owned freshness, independent raw/effective evidence identity, and real adapter execution in both Newsletter and CMPCT domains; universal production adoption and prospective value remain unproven.**
