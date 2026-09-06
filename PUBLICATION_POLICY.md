# Publication safety policy

FCMO AI Newsletter is a **public-only autonomous publication repository**. It is the public sink and clean-room newsroom, not the private research workspace.

## Safety boundary

This repository must contain only material intended for public release. It must never contain private research workspaces, internal agent state, internal project-specific relevance, private hypotheses or experiments, operational logs from a private source, private-source repository history, upstream commit identifiers, personal email addresses, credentials or private keys.

Only a sanitized, semantically declassified, allowlisted public corpus may cross the upstream publication airlock. The committed repository, public newsroom and reader-facing runtime do not fetch or consume raw private research state.

The sole transport exception is `.github/workflows/newswire-bridge.yml`: it may use a short-lived, **read-only** GitHub App token to materialize private ARB in an ephemeral runner directory solely to execute ARB's own tests and deterministic publication/declassification compiler. The bridge deliberately avoids private `actions/checkout` so the private commit identity is not emitted to a public workflow log; private test/build diagnostics are captured off-log. It copies only `_public_release` into runner-temporary storage and **deletes the private checkout before public-side verification or Git staging begins**. An unconditional finalizer removes residual private checkout/log/release state even on failure paths. No raw private checkout, history or operational state may enter the public Git tree.

The absence of an obvious private name is not sufficient evidence that an inference is safe to publish. Strategic ARB implications remain default-private. `tools/newswire_bridge.py` independently verifies the surviving release after the private checkout is gone: exact path allowlist, content-addressed digest/release identity, public IDs, native-edition parity, UTF-8/JSON structure, private/strategic markers, personal-email/runner-path leakage and secret-like material. Public analysis is then reconstructed inside the newsroom from the sanitized evidence package and public sources.

Native Spanish and Simplified Chinese wording crosses the same public boundary as English. Translation does not make private material safe: locale deltas are structurally/privacy checked before transfer and again reconciled against the declassified public schema downstream.

## Safe-fail rule

If upstream tests, semantic declassification, independent transfer verification, privacy, integrity, native-edition parity, media provenance, release validation, frontend validation or live-production validation fails, the public release is not advanced. The previous deployed version remains live. No failed gate may be bypassed merely to refresh the website.

A missing or stale upstream corpus heartbeat is an operational failure. It must not be represented as a healthy quiet-news day. A quiet day is valid only when a fresh airlock receipt proves that the upstream airlock ran and its content-addressed `release_id` is unchanged.

## Autonomous editorial boundary

The public newsroom may:

- ingest independently verified sanitized public dossiers and ARB-authored public locale deltas;
- reconcile/validate those native editions without generating replacement prose;
- reopen and research public sources;
- locate additional public scholarly context;
- produce public-only editorial framing from the public evidence surface;
- resolve reusable visual material with explicit provenance or generate original FCMO explanatory artwork;
- build Story, archive, search, topic, organization, correction, methodology, status and language-gateway frontends;
- publish feeds, sitemaps, structured data and machine surfaces.

It may not:

- use private ARB reasoning as hidden context for public copy;
- call a translation model/API or silently generate a missing locale;
- retrieve private ARB state outside the isolated Newswire Bridge transport job;
- retain the bridge's private checkout after the declassified release has been extracted;
- bypass a missing native edition to keep the site fresh.

Generated FCMO explanatory graphics are editorial illustrations, never source evidence. External story media must have a recorded source page, credit and machine-verifiable reuse basis before the autonomous Visual Desk accepts it.

## Repository structure

- `corpus/` — independently verified sanitized/declassified public handoff, ARB-authored native-edition deltas and `airlock.json`; never raw private research state;
- `site/` — checked-in public base tree, Story routes, shared assets, media, legal pages, newsroom status and native locale packs;
- `release-src/` — editable canonical English release source regenerated from the sanitized corpus, including public research/media receipts;
- `release-overlay/final/` — deterministic frozen package of `release-src/`, hash-checked before assembly;
- `tools/newswire_bridge.py` — independent downstream transfer verifier and atomic `corpus/` staging boundary;
- `tools/sync_airlocked_locales.py` + `tools/validate_localizations.py` — provider-free native-edition import and integrity boundary;
- `tools/build_editorial_frontends.py` + `tools/finalize_editorial_frontends.py` — post-overlay discovery/frontend layer that is rebuilt on the exact Pages candidate;
- `tools/` — ingest, public research, visual, Story, receipt and verification tooling;
- `publish/` — ephemeral assembled deployment candidate, never the authority-bearing source;
- `.github/workflows/newswire-bridge.yml` — read-only App transport: ephemeral ARB validation/build → destroy private checkout → independent public verification → `corpus/`; it owns the daily transport cadence at 07:10 America/Mexico_City;
- `.github/workflows/bootstrap-newsroom.yml` — public-only migration path for the existing published corpus;
- `.github/workflows/daily-refresh.yml` — successful bridge/verified corpus → heartbeat → ingest → locale sync/reconcile/integrity → public research → visual desk → Story/discovery build → ACK → release gates → commit cycle;
- `.github/workflows/pages.yml` — reconstructs the frozen candidate, applies native locales, rebuilds discovery frontends on that exact tree, deploys, then proves the production origin;
- `.github/workflows/newsroom-health.yml` — recurring reality-grounded check of the deployed newspaper.

The public repository's git history remains independent from any private source repository.

## Authentication boundary

The only external activation credential is a least-privilege GitHub App installed only on private `FCMO-AI/AI-Research-Breakthroughs` with repository **Contents: Read-only**. Each bridge run mints a short-lived installation token scoped only to that repository using GitHub's current recommended **Client ID** interface. The App cannot write to either repository.

The public repository stores only the App Client ID as Actions variable `FCMO_NEWSWIRE_APP_CLIENT_ID` and the App's generated PEM private key as encrypted Actions secret `FCMO_NEWSWIRE_APP_PRIVATE_KEY`. The private key must never enter source control or logs. The PEM is consumed only by the token-minting action, not passed through shell preflight; the derived Git authentication header is masked and discarded; and the credential-bearing bridge job is restricted to reviewed `main`.

Once the independently verified public candidate survives the bridge, Newsletter's own `GITHUB_TOKEN` may commit only `corpus/`. No personal publisher token, PAT fallback, translation-provider secret, private Actions runner or second publisher credential is part of the production contract.

Private-repository Actions availability is separate infrastructure debt, not a Newsletter activation dependency. The exact single remaining operator action bundle and completion evidence are recorded in `NEWSWIRE_ACTIVATION_STATUS.md`.

## Operational truth

`site/data/newsroom-status.json` is a downstream acknowledgement, not a substitute for deployment proof. Pre-Pages states deliberately end in `_READY`. Actual production visibility is established by the live oracle against `https://fcmo-ai.github.io/FCMO-AI-Newsletter/`.

The one-time state `BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE` explicitly means the already-public corpus was rebuilt into the autonomous newsroom while no fresh private-source transfer was asserted. It is replaced by the first valid `fcmo-newswire-airlock-v2` delivery.

The complete architecture and evolution contract live in `AUTONOMOUS_NEWSROOM.md`.
