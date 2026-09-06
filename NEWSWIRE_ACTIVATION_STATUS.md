# FCMO AI Newsletter — Newswire Activation Status

**Status:** `AWAITING_GITHUB_APP_ONLY`  
**Launch blocker count:** 1 operator action bundle  
**Launch blocker:** configure the least-privilege GitHub App described below

This is the current launch-status authority. Historical handoff documents remain useful for provenance, but old references to Anthropic translation credentials, personal publisher tokens, private-repository Actions billing, or manual daily refresh are superseded by this contract.

## Mission lock

The Newsletter is considered activation-ready only when the user has exactly one external job: configure the GitHub App. Everything after that must execute from repository code and GitHub automation without a PAT, translation API, private Actions runner, manual workflow dispatch, Pages toggle, or second credential.

The private research repository remains private. The committed public repository remains public-only. The transport bridge may read private ARB only inside one ephemeral job and may persist only the independently verified declassified release.

## DONE

### Upstream publication and editorial contract

- Airlock v2 semantic declassification is merged in private ARB.
- Strategic/private implication fields remain default-private and the final public transfer is positively allowlisted.
- English, Latin American Spanish (`es-419`) and Simplified Chinese (`zh-Hans`) are one upstream publication obligation.
- Native editions are bound to the canonical source revision and declassified public projection and fail closed on stale bindings.
- The first four native Airlock v2 deltas are already authored in ARB.
- Standalone private ARB identity, private project markers, personal identifiers and secret-like material are rejected at transfer boundaries.

### Public newsroom

- Provider-free locale import, reconciliation and deterministic integrity validation are merged.
- Clean-room public re-research, visual desk, Story layer, archive/search/topic/organization/corrections/feed/methodology/editorial-policy/automation/accessibility/status/404 frontends are merged.
- Frozen release, readiness receipt, browser DOM validation, Pages deployment and live-origin oracle are merged.
- Production-health checking is merged.
- Pages is already operational; enabling Pages is not an activation task.

### App-only transport bridge

- `.github/workflows/newswire-bridge.yml` runs on the public repository's GitHub-hosted runner, so private-repository Actions availability is not part of the Newsletter launch path.
- The bridge mints a short-lived GitHub App token scoped only to `FCMO-AI/AI-Research-Breakthroughs` with **Contents: Read-only**.
- The token workflow uses GitHub's current recommended **Client ID** input rather than the legacy App-ID input.
- It checks out private ARB ephemerally without exposing the private commit identity, runs ARB's own unit tests and deterministic publication/declassification build with private diagnostics suppressed from public logs, and creates the upstream `airlock.json` receipt.
- It copies only `_public_release` to runner-temporary storage and destroys the private checkout before public-side verification or Git staging begins; an unconditional finalizer also removes residual private state on failure paths.
- `tools/newswire_bridge.py` independently recomputes the content-addressed digest/release ID; enforces the exact public path allowlist; rejects symlinks, binary/non-UTF8 files, malformed JSON/JSONL, private/strategic markers, personal email, runner paths and secret-like material; validates public IDs; and requires ES/ZH delta parity.
- `corpus/` is replaced only through a verified sibling staging tree, with rollback protection against partial replacement.
- The GitHub App has no write authority. Newsletter's own `GITHUB_TOKEN` may commit **only `corpus/`** after independent verification.
- A successful bridge triggers `daily-refresh.yml` via `workflow_run`; a failed bridge is explicitly rejected by the downstream job guard.
- The newsroom then triggers Pages via the existing `workflow_run` bridge, and Pages must pass the live-origin oracle.
- The bridge owns the daily transport cadence at **07:10 America/Mexico_City**, after the 06:00 ARB research activation has had its expected ~50-minute work window to settle.
- There is no PAT fallback, model-provider translation credential, private Actions runner dependency, manual daily dispatch or second schedule owner.

### Regression protection

- Unit regressions cover valid transfer, digest tampering, private-marker leakage, non-allowlisted files, locale divergence, receipt count drift and atomic corpus replacement.
- Workflow-contract regressions require read-only ARB scope, Client-ID token configuration, main-only secret use, masked auth material, destruction of the private checkout before public verification, unconditional residual cleanup, `corpus/`-only staging, settled daily cadence, successful-bridge chaining, and absence of `actions: write` / API dispatch authority.

## THE ONLY USER ACTION

Create/configure one GitHub App. A useful name is **FCMO Newswire Reader**.

1. Create the App under the FCMO-AI organization (or an account that can install it on the organization repository).
2. Repository permission: **Contents — Read-only**. No write permission is required. No organization permission is required. No webhook is required for this design.
3. Install the App on **only** `FCMO-AI/AI-Research-Breakthroughs`.
4. Generate one private key for the App.
5. In `FCMO-AI/FCMO-AI-Newsletter` Actions configuration, set repository variable `FCMO_NEWSWIRE_APP_CLIENT_ID` to the App's **Client ID**.
6. In the same repository, set encrypted Actions secret `FCMO_NEWSWIRE_APP_PRIVATE_KEY` to the generated PEM private key.

These six configuration details are one credential-activation bundle, not six independent system chores. Once they exist, the repository is designed to take over automatically. Do **not** paste the PEM private key into chat, source control, an issue, or a workflow log.

## AUTOMATICALLY PENDING AFTER THE APP EXISTS

These are intentionally **not** user tasks:

1. scheduled bridge obtains the read-only App token;
2. ARB tests execute on the public runner's ephemeral private checkout;
3. deterministic declassification build produces the public release;
4. private checkout is destroyed;
5. public-side transfer verifier accepts or fails closed;
6. verified `corpus/` is committed;
7. autonomous newsroom ingests and validates the fresh heartbeat;
8. ES/ZH deltas are imported and full three-language parity is proved;
9. public clean-room research, visuals, Story/frontends and readiness receipts rebuild;
10. release gates pass;
11. Pages builds and deploys;
12. live-origin oracle proves the production site matches repository truth;
13. production-health workflow continues recurring verification.

If any post-App step fails, that is an engineering defect or observable platform failure to diagnose from evidence; it is not permission to silently add another manual prerequisite.

## NOT STARTED / DELIBERATELY OUTSIDE LAUNCH

**None launch-critical.**

The historical ARB knowledge reconciliation currently parked in ARB PR #31 is intentionally post-launch work. It is not required for the first Airlock v2 production round-trip and must not be smuggled into the launch merely to make the task list look empty.

The wider FCMO private-repository GitHub Actions runner/billing problem is separate infrastructure debt. The Newsletter transport no longer depends on it. Restoring private Actions remains valuable for ARB and other private repositories, but it is not a prerequisite the Newsletter user must complete to activate publication.

## Completion evidence required after activation

Do not change this status to `ACTIVE` merely because the App token can be minted. Require all of:

- a successful `Pull airlocked newswire with GitHub App` run with real executed steps;
- a committed `corpus/airlock.json` whose content identity passes the downstream verifier;
- successful autonomous newsroom ACK for the same release identity;
- successful Pages deployment;
- successful live-origin oracle against `https://fcmo-ai.github.io/FCMO-AI-Newsletter/`;
- the expected new native-language Story surfaces visible in production.

Until those facts exist, the honest state remains `AWAITING_GITHUB_APP_ONLY`.
