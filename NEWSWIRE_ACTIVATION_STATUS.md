# FCMO AI Newsletter — Newswire Activation Status

**Status:** `RECOVERY_IN_PROGRESS`  
**Operator blocker count:** 0  
**Engineering blocker:** first successful Airlock v2 production round-trip has not yet been demonstrated

This is the current launch-status authority. Historical handoff documents remain useful for provenance, but old references to Anthropic translation credentials, personal publisher tokens, private-repository Actions billing, manual daily refresh, or an unconfigured GitHub App are superseded by this contract.

## Mission lock

The user-side GitHub App setup is complete and has been proven in a real workflow: the Client ID was accepted, a read-only installation token was minted, and private ARB was cloned successfully. Everything after that is an engineering responsibility. No PAT, translation API, private Actions runner, manual workflow dispatch, Pages toggle, or second credential may be introduced as a workaround.

The private research repository remains private. The committed public repository remains public-only. The bridge may read one immutable ARB snapshot only inside an ephemeral job and may persist only an independently verified declassified release.

## PROVEN WORKING

### GitHub App transport boundary

- The GitHub App is installed and functional with **Contents: Read-only** on `FCMO-AI/AI-Research-Breakthroughs`.
- A real bridge run successfully minted the token and cloned private ARB; credentials are therefore no longer a launch hypothesis or operator blocker.
- The App has no public-repository write authority. Newsletter's own `GITHUB_TOKEN` remains constrained to the public sink.

### Public newsroom / last-known-good serving

- Pages is operational and the production oracle has verified the currently deployed three-language newsroom.
- English, Latin American Spanish (`es-419`) and Simplified Chinese (`zh-Hans`) are supported as curated native editions.
- Public clean-room research, Story/frontends, archive/search/topic/organization/corrections/feed/methodology/editorial-policy/automation/accessibility/status surfaces and machine routes are merged.
- The failed activation did not modify `corpus/`; downstream refresh/Pages correctly failed closed and the last-known-good public site stayed available.

### Privacy and declassification boundary

- Strategic/private implication fields remain default-private and the final public transfer is positively allowlisted.
- Native editions are bound to canonical source bytes plus the declassified English projection and fail closed on stale bindings.
- Standalone private ARB identity, private project markers, personal identifiers, runner paths and secret-like material are rejected at transfer boundaries.
- The private checkout is destroyed before public verification or Git staging begins, including failure paths.

## RECOVERY CHANGES NOW REQUIRED / IN FLIGHT

1. **Canonical runtime seal on ARB `main`.** Publication tooling belongs on the canonical main lineage, not on a divergent `publication-ready` branch.
2. **Immutable snapshot transaction.** The bridge may discover `main`, but must capture exactly one HEAD and detach it before validation; later research commits cannot change that transaction.
3. **One atomic upstream authority.** `tools/publication_seal.py` must own unit contracts, real public-input validation, importance validation, deterministic declassification build, native locales and Airlock receipt.
4. **Privacy-safe diagnostics.** Failures may expose only stable `SEAL_FAIL:<CLASS>` codes, never private assertions/records/paths.
5. **Best-effort scheduler mitigation.** Multiple staggered idempotent attempts replace reliance on a single daily cron delivery.
6. **Health split.** Serving availability and autonomous-publication freshness are separate truths; a stale/bootstrap release may remain safely online while freshness is red.

## CURRENT PRODUCTION TRUTH

The system is **not `ACTIVE` yet**. The last attempted automated bridge failed before Airlock creation, while the public site continued to serve the previous bootstrap release. This is a safe failure, not a successful activation.

The historical ARB knowledge reconciliation parked in ARB PR #31 remains deliberately post-launch. The wider private-repository GitHub Actions runner/billing problem also remains separate infrastructure debt; Newsletter transport does not depend on it.

## Completion evidence required

Do not change this status to `ACTIVE` until one real run proves the complete identity chain without manual rescue:

- `Pull airlocked newswire with GitHub App` executes automatically and succeeds;
- the private source is one immutable ARB `main` snapshot and the runtime publication seal returns `SEAL_OK`;
- `corpus/airlock.json` is committed and independently verifies as `fcmo-newswire-airlock-v2`;
- the public commit changes only `corpus/`;
- autonomous newsroom refresh succeeds for the same release identity;
- Pages deploys that release;
- the live-origin oracle sees the same release and passes reader/machine routes;
- the expected Story identity is available in EN, `es-419` and `zh-Hans`;
- production freshness is green as well as serving health.

Until all of those facts exist, the honest state remains `RECOVERY_IN_PROGRESS`.
