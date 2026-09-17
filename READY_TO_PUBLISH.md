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
- Front-end SHA-256: `c39f8fb087e40d4306b5b2ba968963efa9d999ba6b71ad61e9420aefe3ddb5b3`
- Release archive SHA-256: `c3b2ea464608ff36032210757b7244fb3065a66821017fb4c4aafa8a8df60fa9`
- Encoded release payload SHA-256: `5ec4c30c9da1c9e7c5b05bd8d3a320122684c9246a34adf13f2d03a49047440f`
- 36/36 release payload parts present; payload and archive checked by SHA-256
- 717 public files after assembly
- 43 canonical dossiers
- 43 stable dossier routes
- 19 frozen edition routes
- 10 vetted sourced story visuals + 33 embedded editorial fallbacks

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
- 43 dossier identifiers and stable human routes;
- 19 edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`fcmo-agent-discovery-v2`, `fcmo-agent-query-v2`);
- final 10/33 story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic post-frontend build-manifest generation.

The release assembler, native-locale gate, and discovery frontend builder were rerun; the assembled public candidate measures:

`FCMO AI Newsletter signal-field-v4.1.1-viewport-polish READY: 717 public files; index c39f8fb087e4…`

## Daily refresh readiness

The update path is fail-closed: ARB supplies a sanitized public corpus plus any agent-authored `es-419`/`zh-Hans` deltas, Newsletter requires exact three-language story parity, rebuilds public research/media/Story/discovery surfaces, freezes the canonical overlay, regenerates this receipt, and reruns the release gates before a commit can deploy. There is no downstream translation provider or generative fallback. Platform runner/billing availability and the GitHub App installation credential are external prerequisites; their absence must stop an update rather than weaken the publication boundary.

## GitHub Pages

Pages reconstructs the frozen candidate, applies committed native locales, regenerates deterministic discovery frontends on that exact candidate, and deploys only after the build job succeeds. The deployment workflow also listens to completed autonomous-newsroom workflows so a bot-authored refresh can reach Pages without relying on a second `push` event.
