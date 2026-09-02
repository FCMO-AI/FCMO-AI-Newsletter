# FCMO AI Newsletter — ready to publish

Release: **Signal Field v4.1 final**

The private repository is intentionally staged so the publication release is assembled from a hash-verified overlay at deploy time. `main` contains the release machinery; the final public artifact is not dependent on private research state or external build services.

## Final manual action

Change the repository visibility from **Private** to **Public**.

The Pages workflow listens for GitHub's `public` repository event and will assemble, validate, upload, and deploy the frozen release to:

**https://fcmo-ai.github.io/FCMO-AI-Newsletter/**

## Release identity

- Front-end SHA-256: `122db0badc0142e6f2b03e22ea36851a103d03ce778f07cc10b5741fb80253bf`
- Source prelaunch bundle SHA-256: `93c1294eaff05eba9bad0c1c90c25af127ddbb0e8a7b4b6663b6c39b0c3881b0`
- 22 canonical dossiers
- 22 stable dossier routes
- 3 frozen edition routes
- 14 vetted sourced story visuals + 8 embedded editorial fallbacks
- 99 route/viewport QA checks
- 0 graph collisions
- 0 JavaScript failures
- 0 overflow failures
- 0 blank-route failures
- 0 tiny-text failures
- 0 broken-image failures

## GitHub Pages note

GitHub currently reports `has_pages: false` while the repository is private. The deployment workflow is already present and will run on the visibility-change event. If GitHub requires first-time Pages activation for this organization, the only possible platform-side follow-up is **Settings → Pages → Source: GitHub Actions** and then rerun **Deploy FCMO AI Newsletter**. This cannot be pre-enabled with the repository's normal `GITHUB_TOKEN`; GitHub requires separate administration permission for first-time Pages enablement.
