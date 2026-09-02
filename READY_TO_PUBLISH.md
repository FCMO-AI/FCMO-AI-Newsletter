# FCMO AI Newsletter — ready to publish

Release: **Signal Field v4.1 final**

Status: **release-ready after two independent pre-publication verification passes.**

The private repository is staged so the publication release is assembled from a frozen, hash-verified overlay at deploy time. `main` contains only the public base tree, release package, validation tooling, legal/publication scaffold, and deployment workflow needed for the public site. No private research state is required at build time.

## Final manual action

Change the repository visibility from **Private** to **Public**.

The Pages workflow listens for GitHub's `public` repository event and will reconstruct, validate, upload, and deploy the frozen release to:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

Do not manually copy a different `index.html` into Pages or bypass the release validator; the frozen release identity below is the canonical candidate.

## Release identity

- Release manifest schema: `fcmo-ai-newsletter-release-overlay-v2`
- Release: `signal-field-v4.1-final`
- Front-end SHA-256: `122db0badc0142e6f2b03e22ea36851a103d03ce778f07cc10b5741fb80253bf`
- Release archive SHA-256: `de6e6aa2bec5667106a4c43c1ed79fd4d2193fdc8f4593ddb6bc9ef1efb1d2bd`
- Encoded release payload SHA-256: `ba63bdc2b1922b224b9e0dfc32f0a594cf7655865074ba61b88d79f5fed336da`
- Source prelaunch bundle SHA-256: `93c1294eaff05eba9bad0c1c90c25af127ddbb0e8a7b4b6663b6c39b0c3881b0`
- 14/14 release payload parts present and Git-object verified
- 82 public files after assembly
- 22 canonical dossiers
- 22 stable dossier routes
- 3 frozen edition routes
- 14 vetted sourced story visuals + 8 embedded editorial fallbacks

## Verification receipts

### Visual/browser QA

- 99 route/viewport checks
- 0 Signal Field graph collisions
- 0 JavaScript failures
- 0 overflow failures
- 0 blank-route failures
- 0 tiny-text failures
- 0 broken-image failures
- mobile hero hierarchy and navigation cue verified after fixes

### Release/data QA

The final assembler validates, before deployment:

- exact release archive and front-end hashes;
- archive path/symlink safety;
- required human and machine-readable public files;
- 22 dossier identifiers and stable human routes;
- 3 edition JSON/HTML routes;
- JSON, JSONL, RSS, and sitemap parsing;
- agent discovery/query contracts (`fcmo-agent-discovery-v2`, `fcmo-agent-query-v2`);
- final 14/8 story-media policy;
- credential-like strings and personal-mailbox leakage;
- remote JavaScript and remote stylesheet dependencies while allowing legitimate canonical/feed/discovery links and vetted story imagery;
- deterministic build-manifest generation.

The release assembler was rerun after correcting the dependency validator and returned:

`FCMO AI Newsletter signal-field-v4.1-final READY: 82 public files; index 122db0badc01…`

## GitHub Actions note

GitHub Actions jobs in the private repository have repeatedly failed **before a runner or workflow step was assigned** (`runner_id: 0`, empty step list). The same release logic has therefore been executed directly against the frozen artifacts as an independent pre-publication gate. This is not a recorded application/test failure.

Once the repository is public, public GitHub-hosted Actions should be able to run the prepared deployment workflow normally.

## GitHub Pages note

GitHub currently reports Pages as not yet enabled while the repository is private. The deployment workflow is already present and listens for the visibility-change event. If GitHub requires first-time Pages activation for this organization, the only platform-side follow-up is:

**Settings → Pages → Source: GitHub Actions**, then **Actions → Deploy FCMO AI Newsletter → Run workflow**.

GitHub's standard workflow token cannot pre-enable first-time Pages for a private repository because that operation requires separate administration/Pages permission.
