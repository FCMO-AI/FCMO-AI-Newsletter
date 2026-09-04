# FCMO AI Newsletter — ready to publish

Release: **Signal Field v4.1 final**

Status: **release-ready after the assembler, curated-localization gate, and DOM verification pass.**

Receipt measurement: **2026-09-02T19:57:43.686Z** (UTC), using `_audit/verificar-legal.mjs` and Microsoft Edge.

The private repository is staged so the publication release is assembled from a frozen, hash-verified overlay at deploy time. `main` contains only the public base tree, release package, validation tooling, legal/publication scaffold, and deployment workflow needed for the public site. No private research state is required at build time.

## Final manual action

Change the repository visibility from **Private** to **Public**.

The Pages workflow listens for GitHub's `public` repository event and will reconstruct, validate, upload, and deploy the frozen release to:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Do not manually copy a different `index.html` into Pages or bypass the release validator; the frozen release identity below is the canonical candidate.

## Release identity

- Release manifest schema: `fcmo-ai-newsletter-release-overlay-v2`
- Release: `signal-field-v4.1-final`
- Front-end SHA-256: `8383e0c1d9ff6c377e537446c0203e3dfa85903226987d90bdbdfa7d440fc11f`
- Release archive SHA-256: `0387d68ed93b1f0668efc0e53191fb45606091123e041f5c914b44756edc986b`
- Encoded release payload SHA-256: `e1eca7e0fe4c243d0cf3271a140764e1b7f34a275380e4d220c0df49c606a479`
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

`FCMO AI Newsletter signal-field-v4.1-final READY: 98 public files; index 8383e0c1d9ff…`

## GitHub Actions note

GitHub Actions jobs in the private repository have repeatedly failed **before a runner or workflow step was assigned** (empty runner and step metadata). The same release logic has therefore been executed directly against the frozen artifacts as an independent pre-publication gate. This is not a recorded application/test failure.

Once the repository is public, public GitHub-hosted Actions should be able to run the prepared deployment workflow normally.

## GitHub Pages note

GitHub currently reports Pages as not yet enabled while the repository is private. The deployment workflow is already present and listens for the visibility-change event. If GitHub requires first-time Pages activation for this organization, the only platform-side follow-up is:

**Settings → Pages → Source: GitHub Actions**, then **Actions → Deploy FCMO AI Newsletter → Run workflow**.

GitHub's standard workflow token cannot pre-enable first-time Pages for a private repository because that operation requires separate administration/Pages permission.
