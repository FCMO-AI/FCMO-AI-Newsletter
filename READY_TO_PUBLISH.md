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
- Front-end SHA-256: `12d0d6855924d8b97e3fafdfbed71e34bd617d35805539e3b6ccb50fc87cf41e`
- Release archive SHA-256: `e09445d785240add2b5dd1dbf15f0c09878ddfa372dcfa80d19a211804d19b7f`
- Encoded release payload SHA-256: `03cf70d4e87cab7cffb8142ca1c546f73222998452a76229587e8c8c86702a34`
- 37/37 release payload parts present; payload and archive checked by SHA-256
- 732 public files after assembly
- 44 canonical dossiers
- 44 stable dossier routes
- 20 frozen edition routes
- 10 vetted sourced story visuals + 34 embedded editorial fallbacks

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
- 44 dossier identifiers and stable human routes;
- 20 edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`fcmo-agent-discovery-v2`, `fcmo-agent-query-v2`);
- final 10/34 story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic post-frontend build-manifest generation.

The release assembler, native-locale gate, and discovery frontend builder were rerun; the assembled public candidate measures:

`FCMO AI Newsletter signal-field-v4.1.1-viewport-polish READY: 732 public files; index 12d0d6855924…`

## Daily refresh readiness

The update path is fail-closed: ARB supplies a sanitized public corpus plus any agent-authored `es-419`/`zh-Hans` deltas, Newsletter requires exact three-language story parity, rebuilds public research/media/Story/discovery surfaces, freezes the canonical overlay, regenerates this receipt, and reruns the release gates before a commit can deploy. There is no downstream translation provider or generative fallback. Platform runner/billing availability and the GitHub App installation credential are external prerequisites; their absence must stop an update rather than weaken the publication boundary.

## GitHub Pages

Pages reconstructs the frozen candidate, applies committed native locales, regenerates deterministic discovery frontends on that exact candidate, and deploys only after the build job succeeds. The deployment workflow also listens to completed autonomous-newsroom workflows so a bot-authored refresh can reach Pages without relying on a second `push` event.
