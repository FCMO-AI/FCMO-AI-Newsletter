# FCMO AI Newsletter — public release receipt

Release: **Signal Field v4.1 final**

Status: **public release assembled, native-localized, validated, and deployable through GitHub Pages.**

Receipt measurement: **2026-09-02T19:57:43.686Z** (UTC), using `_audit/verificar-legal.mjs` and Microsoft Edge.

This repository is the public publication sink. `site/` supplies the public base, `release-src/` holds the editable canonical release source, `release-overlay/final/` freezes that source deterministically, and deployment assembles only the validated `publish/` candidate. No private research workspace is required to build or serve the site.

## Publication state

The public site is deployed at:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Ordinary releases require no repository-visibility step. A candidate that fails release integrity, privacy, or native-edition validation is not deployed; the previous public version remains live.

## Release identity

- Release manifest schema: `fcmo-ai-newsletter-release-overlay-v2`
- Release: `signal-field-v4.1-final`
- Front-end SHA-256: `196ddb9f1adac9b6624533515e5f523016373d85a94527a84cecd4b1b05cff62`
- Release archive SHA-256: `de0040a34ba14c974b0c1406da36d8f0beceaaf382425e4cb9f1e731373588ca`
- Encoded release payload SHA-256: `ebec42cd1f5ec989b5e5b64d12d8645eb5a02548b88b822ca42bdbe03f1ac6b7`
- 15/15 release payload parts present; payload and archive checked by SHA-256
- 359 public files after assembly
- 23 canonical dossiers
- 23 stable dossier routes
- 3 frozen edition routes
- 3 vetted sourced story visuals + 20 embedded editorial fallbacks

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
- the post-overlay archive/search/topic/organization/methodology/status frontend suite;
- 23 dossier identifiers and stable human routes;
- 3 edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`fcmo-agent-discovery-v2`, `fcmo-agent-query-v2`);
- final 3/20 story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic post-frontend build-manifest generation.

The release assembler, native-locale gate, and discovery frontend builder were rerun; the assembled public candidate measures:

`FCMO AI Newsletter signal-field-v4.1-final READY: 359 public files; index 196ddb9f1ada…`

## Daily refresh readiness

The update path is fail-closed: ARB supplies a sanitized public corpus plus any agent-authored `es-419`/`zh-Hans` deltas, Newsletter requires exact three-language story parity, rebuilds public research/media/Story/discovery surfaces, freezes the canonical overlay, regenerates this receipt, and reruns the release gates before a commit can deploy. There is no downstream translation provider or generative fallback. Platform runner/billing availability and the GitHub App installation credential are external prerequisites; their absence must stop an update rather than weaken the publication boundary.

## GitHub Pages

Pages reconstructs the frozen candidate, applies committed native locales, regenerates deterministic discovery frontends on that exact candidate, and deploys only after the build job succeeds. The deployment workflow also listens to completed autonomous-newsroom workflows so a bot-authored refresh can reach Pages without relying on a second `push` event.
