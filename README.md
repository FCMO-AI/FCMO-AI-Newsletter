# FCMO AI Newsletter

**What actually matters in AI — carefully researched and curated by FCMO.**

**Publication:** https://fcmo-ai.github.io/FCMO-AI-Newsletter/

FCMO AI Newsletter is an evidence-conscious autonomous publication and public research corpus covering important developments across artificial intelligence research, models, systems, hardware, robotics, policy, geopolitics, business, and the broader AI ecosystem.

The publication separates evidence quality, confidence, limitations, contradictions, and potential importance rather than treating every headline as equally established. It is designed for quick human reading while preserving enough structured context for deeper research and software-agent use.

## Public publication model

The release is deterministic and fail-closed:

- ARB prepares the public evidence record and all three native editorial editions. The isolated Newswire Bridge uses a **read-only GitHub App** to check out ARB ephemerally on a public GitHub-hosted runner, runs ARB's own tests and deterministic declassification compiler there, copies only `_public_release`, destroys the private checkout, and independently re-verifies the allowlisted artifact before `corpus/` can change.
- `tools/newswire_bridge.py` reproduces the upstream content digest and release identity, rejects non-allowlisted paths, private/strategic markers, secret-like material, personal-email/runner-path leakage, malformed JSON/JSONL, invalid public IDs and ES/ZH delta divergence. `corpus/` is replaced through a verified staging directory rather than mixed in place.
- `site/` is the checked-in public base tree.
- `release-overlay/final/` is the frozen, hash-verified English canonical release payload.
- `tools/apply_final_release.py` reconstructs the canonical publication candidate, validates its hashes and public-data contract, scans for credential/privacy leaks and unsafe remote executable dependencies, and writes a deterministic build manifest.
- `tools/sync_airlocked_locales.py` imports ARB-authored Spanish and Simplified Chinese deltas; `tools/validate_localizations.py` requires complete provider-free three-language coverage and preserves structural/numeric/ID/URL invariants.
- `tools/apply_curated_i18n.py` applies the committed native-language presentation only after the canonical English release passes its integrity gate.
- `tools/build_editorial_frontends.py` and `tools/finalize_editorial_frontends.py` generate archive, local search, topics, organization indexes/details, corrections, feeds, methodology, editorial policy, automation disclosure, accessibility, status, 404 and the native-edition gateway on the **exact post-overlay Pages candidate**.
- `.github/workflows/newswire-bridge.yml` owns the upstream cadence at **07:10 America/Mexico_City**, after the 06:00 ARB research activation has had its expected work window to settle. A successful bridge run triggers the autonomous newsroom through `workflow_run`; the newsroom in turn triggers Pages. This avoids recursive `GITHUB_TOKEN` push assumptions and avoids a second independent refresh schedule.
- `.github/workflows/pages.yml` deploys only the validated `publish/` directory to GitHub Pages, then `tools/verify_live_newsroom.py` checks the production origin itself.
- A failed bridge, release, locale-integrity, frontend, browser or live-origin validation prevents the new candidate from being considered healthy rather than publishing a partial or drifted edition.
- No private research workspace, private operational state, translation API or runtime model provider is required to build or serve the public release. Private ARB bytes exist only inside the isolated transport runner and are deleted before public-side staging begins, with an unconditional cleanup path on failures.

`data/relationships.json` and `data/relationships.jsonl` are equivalent public surfaces: the JSON is an array and the JSONL is one identical object per line. They must contain the same objects in the same order; clients may choose either representation.

The release identity and measured publication receipt are recorded in `READY_TO_PUBLISH.md` and `release-overlay/final/manifest.json`.

## Native languages

FCMO AI Newsletter natively supports exactly three publication languages:

- **English (`en`)** — canonical semantic source;
- **Latin American Spanish (`es-419`)** — source-controlled native editorial edition;
- **Simplified Chinese (`zh-Hans`)** — source-controlled native editorial edition.

The ARB research/publication agent that already understands a story's evidence prepares the English, Spanish and Chinese wording as **one publication obligation** before the material crosses the airlock. Newsletter does not call a second model to reconstruct that understanding later.

Every public news record must have Spanish and Chinese coverage for the reader-facing prose rendered by the publication, including deep dossier fields that materially affect interpretation. The selector resolves an explicit `?lang=` request first, then a saved manual choice, then browser language, with English as the final fallback.

Runtime performs presentation lookup only. There is no translation service, generative fallback, or page-view language API. Missing native-edition material is a release defect. English remains directly selectable as the authority-bearing semantic source; Spanish and Chinese are native editorial views of that same evidence record, with stable IDs, numbers, evidence status and provenance preserved.

The complete source-control, curation, provenance, and validation contract is documented in [`LOCALIZATION.md`](LOCALIZATION.md).

## Human and agent surfaces

The publication exposes a front page plus first-class archive, search, topics, organizations, corrections, feeds/data, methodology, editorial-policy, automation, accessibility, status and EN/ES/ZH Story surfaces. Topic and organization index entries have durable detail routes instead of terminating at category shells.

The same sanitized public corpus is exposed in machine-readable form through stable `FCMO-<12 uppercase hex>` identifiers, per-brief JSON dossiers, public search data, Story JSON, feeds, publication memory, relationship data, sitemaps, `agent.json`, `llms.txt`, and `llms-full.txt`.

Potential impact and confidence are deliberately separate: a spectacular claim can be important *if true* while still being weakly supported, and an incremental result can be extremely well established without being field-changing.

## Automation and authentication

The only external activation credential is a least-privilege **GitHub App** installed only on private `FCMO-AI/AI-Research-Breakthroughs` with repository **Contents: Read-only**. Newsletter stores its App **Client ID** as the repository Actions variable `FCMO_NEWSWIRE_APP_CLIENT_ID` and the generated private key as the encrypted Actions secret `FCMO_NEWSWIRE_APP_PRIVATE_KEY`; each bridge run mints a short-lived installation token scoped only to ARB. The workflow uses GitHub's current recommended Client-ID input rather than the legacy App-ID input.

The App cannot write to ARB or Newsletter. Its PEM is consumed only by the token-minting action, not passed through shell preflight. The bridge also masks its derived Git authentication header, suppresses private ARB test/build diagnostics from the public workflow log, and only runs the credential-bearing job from reviewed `main`.

After ARB's own tests and declassification compiler run in the isolated checkout, the checkout is deleted. The surviving public artifact passes `tools/newswire_bridge.py` independently, and only then may Newsletter's own `GITHUB_TOKEN` atomically update `corpus/`.

This makes private-repository GitHub Actions availability **non-blocking** for Newsletter publication. There is no PAT fallback, translation-provider credential, private runner requirement, manual daily dispatch or second publisher credential in the launch contract.

The public newsroom, generated site and committed repository never receive raw private ARB state. The only component allowed to read ARB is the isolated Newswire Bridge transport step, and its output boundary remains strictly one-way and public-only.

See [`NEWSWIRE_ACTIVATION_STATUS.md`](NEWSWIRE_ACTIVATION_STATUS.md) for the exact activation contract and completion ledger.

## FCMO AI leadership and attribution

FCMO AI material uses contribution-based attribution. Organizational rank does not substitute for authorship.

For FCMO AI projects and publications, the canonical public order is:

1. **Matías Peña Szőke** — Director, FCMO AI / Head of AI & Technology.
2. **Javier Castellanos Peña** — Founder, FCMO Group.

FCMO Group is the broader project and public-facing umbrella brand. Javier's founder role is recognized at that level; it does not imply authorship of FCMO AI work he did not materially create or acquire rights to.

The titles above are functional public-facing descriptions rather than representations of formally appointed corporate offices while FCMO is not a separate legal entity.

See `ATTRIBUTION.md` for the canonical attribution rules used by this repository and its generated publication.

## Licensing and legal scaffold

This repository uses a mixed-license model so software and editorial material are treated appropriately:

- **Software code:** MIT License — see `LICENSE`. The default repository notice is `Copyright (c) 2026 Matías Peña Szőke and contributors`.
- **Original FCMO AI editorial content:** Creative Commons Attribution 4.0 International (CC BY 4.0) when the project has authority to license it and no more specific notice applies — see `CONTENT_LICENSE.md`.
- **Third-party material:** remains subject to its original copyright, license, trademark, and other applicable rights.
- **FCMO branding:** the FCMO Group, FCMO AI, and FCMO AI Newsletter names, logos, and visual identity are not licensed for reuse merely because repository code or editorial text is openly licensed.

The website legal/disclosure scaffold is defined in `LEGAL_REQUIREMENTS.md`, with baseline public-language templates in `legal/PRIVACY.md` and `legal/DISCLAIMER.md`.

Generated editions expose compact links for About, Feeds & data, Privacy, License, and Disclaimer. Primary and authoritative source links are provided from the relevant research pages and editions.
