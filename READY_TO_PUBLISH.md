# FCMO AI Newsletter — public release receipt

Release: **Signal Field v4.1 final**

Status: **public release assembled, localized, validated, and deployable through GitHub Pages.**

Receipt measurement: **2026-09-02T19:57:43.686Z** (UTC), using `_audit/verificar-legal.mjs` and Microsoft Edge.

This repository is the public publication sink. `site/` supplies the public base, `release-src/` holds the editable canonical release source, `release-overlay/final/` freezes that source deterministically, and deployment assembles only the validated `publish/` candidate. No private research workspace is required to build or serve the site.

## Publication state

The public site is deployed at:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Ordinary releases require no repository-visibility step. A candidate that fails release integrity, privacy, or curated-localization validation is not deployed; the previous public version remains live.

## Release identity

- Release manifest schema: `fcmo-ai-newsletter-release-overlay-v2`
- Release: `signal-field-v4.1-final`
- Front-end SHA-256: `74e28dfd859302cec3afeb43a39b8644dd6e54171a6a5e4d716a543bcfdd372c`
- Release archive SHA-256: `58c608011f59d07082aa17ea3916a99ab5a18029e6705c7e34498f2f6b4a6a62`
- Encoded release payload SHA-256: `bc4b4cd1b1074bc30df87c9c1ade34615f2ee1e001dfa9efb6151ebc7f5b2d79`
- 15/15 release payload parts present; payload and archive checked by SHA-256
- 98 public files after assembly
- 23 canonical dossiers
- 23 stable dossier routes
- 3 frozen edition routes
- 14 vetted sourced story visuals + 9 embedded editorial fallbacks

## Verification receipts

### Visual/browser QA

Measured on **2026-09-02T19:57:43.686Z** with **Microsoft Edge** by `_audit/verificar-legal.mjs`:

- 78 route/viewport checks at 390px and 1440px
- 0 JavaScript failures
- 0 overflow failures
- 0 blank-route failures
- 21 legal DOM checks
- 18 curated-i18n DOM checks

### Release/data QA

The final assembler validates, before deployment:

- exact release archive and front-end hashes;
- archive path/symlink safety;
- required human and machine-readable public files;
- 23 dossier identifiers and stable human routes;
- 3 edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`fcmo-agent-discovery-v2`, `fcmo-agent-query-v2`);
- final 14/9 story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic build-manifest generation.

The release assembler and curated-localization gate were rerun; the assembled public candidate measures:

`FCMO AI Newsletter signal-field-v4.1-final READY: 98 public files; index 74e28dfd8593…`

## Daily refresh readiness

The code path for a daily update is fail-closed: a sanitized public corpus is ingested, missing curated locales are produced before publication, the frozen overlay and this receipt are rebuilt, and the same release gates run before a commit can deploy. Platform credentials or runner/billing availability are external prerequisites; their absence must stop an update rather than weaken the publication boundary.

## GitHub Pages

Pages deploys only the assembled `publish/` artifact after the build job succeeds. The deployment workflow also listens to the completed daily-refresh workflow so a bot-authored refresh can reach Pages without relying on a second `push` event.
