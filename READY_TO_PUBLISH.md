# FCMO AI Newsletter — public release receipt

Release: **Signal Field v4.1.1 Viewport polish**

Status: **public release assembled, native-localized, validated, and deployable through GitHub Pages.**

Receipt measurement: **2026-09-10T07:19:28.381Z** (UTC), using `tests/oraculos/verificar_layout.py + tests/oraculos/verificar_dom.py` and Google Chrome 152.0.7977.64.

This repository is the public publication sink. `site/` supplies the public base, `release-src/` holds the editable canonical release source, `release-overlay/final/` freezes that source deterministically, and deployment assembles only the validated `publish/` candidate. No private research workspace is required to build or serve the site.

## Publication state

The public site is deployed at:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Ordinary releases require no repository-visibility step. A candidate that fails release integrity, privacy, or native-edition validation is not deployed; the previous public version remains live.

## Release identity

- Release manifest schema: `fcmo-ai-newsletter-release-overlay-v2`
- Release: `signal-field-v4.1.1-viewport-polish`
- Front-end SHA-256: `b3c9f4c47073f9be587f86972565757b5ec29580769949728db279fa54a4c8a8`
- Release archive SHA-256: `78974ac7ee48f665a5ac89b3336772a7784a7c072f14e31c0d11aeb61550bf3d`
- Encoded release payload SHA-256: `86c01cdb69a335daf953941a07d5a37f9d16b2f35f841c83d3bb4fd0364deaf8`
- 38/38 release payload parts present; payload and archive checked by SHA-256
- 762 public files after assembly
- 46 canonical dossiers
- 46 stable dossier routes
- 25 frozen edition routes
- 11 vetted sourced story visuals + 35 embedded editorial fallbacks

## Verification receipts

### Visual/browser QA

Measured on **2026-09-10T07:19:28.381Z** with **Google Chrome 152.0.7977.64** by `tests/oraculos/verificar_layout.py + tests/oraculos/verificar_dom.py`:

- 12 route/viewport checks at 390px, 1152px, 1280px, 1366px, 1440px, and 1920px
- 0 JavaScript failures
- 0 overflow failures
- 0 blank-route failures
- 0 legal DOM checks
- 8 curated-i18n DOM checks

### Release/data QA

The final assembler validates, before deployment:

- exact release archive and front-end hashes;
- archive path/symlink safety;
- required human and machine-readable public files;
- the post-overlay archive/search/topic/organization/methodology/status frontend suite;
- 46 dossier identifiers and stable human routes;
- 25 edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`fcmo-agent-discovery-v2`, `fcmo-agent-query-v2`);
- final 11/35 story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic post-frontend build-manifest generation.

The release assembler, native-locale gate, and discovery frontend builder were rerun; the assembled public candidate measures:

`FCMO AI Newsletter signal-field-v4.1.1-viewport-polish READY: 762 public files; index b3c9f4c47073…`

## Daily refresh readiness

The update path is fail-closed: ARB supplies a sanitized public corpus plus any agent-authored `es-419`/`zh-Hans` deltas, Newsletter requires exact three-language story parity, rebuilds public research/media/Story/discovery surfaces, freezes the canonical overlay, regenerates this receipt, and reruns the release gates before a commit can deploy. There is no downstream translation provider or generative fallback. Platform runner/billing availability and the GitHub App installation credential are external prerequisites; their absence must stop an update rather than weaken the publication boundary.

## GitHub Pages

Pages reconstructs the frozen candidate, applies committed native locales, regenerates deterministic discovery frontends on that exact candidate, and deploys only after the build job succeeds. The deployment workflow also listens to completed autonomous-newsroom workflows so a bot-authored refresh can reach Pages without relying on a second `push` event.
