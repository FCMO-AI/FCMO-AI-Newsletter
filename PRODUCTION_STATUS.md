# FCMO AI Newsletter — Production Status

**Canonical operating state:** `OPERATIONAL — DAILY AUTONOMOUS PUBLICATION ACTIVE`

This file records durable product-level truth. It does not replace the live
oracles or health workflows; if those disagree with this document, the live
oracles and current production evidence win.

## First fully proven fresh autonomous production cycle

On 2026-09-13 America/Mexico_City / 2026-09-14 UTC, the production chain completed
end-to-end with no manual publication step:

`ARB publication-ready research -> authenticated sanitized Airlock -> public corpus -> autonomous newsroom -> Story layer -> freshness selection -> publication gates -> GitHub Pages deploy -> live-origin verification -> real-browser EN/ES/ZH verification -> production health`

Proven release:

- Airlock / public release ID: `newswire-130b574a588ef657cab9b862`
- Public Story count: `42`
- Newsroom state: `PUBLIC_DELTA_READY`
- Pages deployment workflow run: `34802301996`
- Build: `success`
- GitHub Pages deploy: `success`
- Live production oracle: `success`
- Reader-visible lead: `FCMO-FAD9D0AFD3E4` — OpenAI Navier–Stokes formalization story
- Production-health workflow run: `34802383824`
- Serving health: `success`
- Publication freshness: `success`
- Editorial freshness: `HEALTHY`
- Measured lead age at health check: about `0.57 h`
- Measured newest-material age: about `0.57 h`
- Measured Airlock age: about `0.61 h`

## Freshness contract

The operating objective is not merely that repository files change. Success means
that the actual public GitHub Pages newspaper receives legitimate new material
with a practical delay of one day or less, and normally much less when ARB already
has publishable evidence.

Production health enforces:

- target front-page material age: `<= 24 h` when eligible material exists;
- acceptable fallback: `<= 48 h` only when the recent window contains no eligible
  material at the configured evidence/materiality threshold;
- fresh authenticated Airlock and newsroom heartbeat;
- live reader routes and deployed release identity;
- real-browser verification of the current lead.

A repository-only update is **not** a successful publication.

## Fail-closed multilingual behavior

English remains the canonical semantic edition. Spanish and Simplified Chinese
remain first-class editions, but a truthful translation backlog no longer freezes
fresh English publication. Missing native translations must be explicitly marked
`pending`, expose a localized pending notice, and link to the canonical English
article. A fake English fallback presented as a native translation is forbidden.

## Recovery behavior

The deterministic Pages publication workflow retries the current valid candidate
on a two-hour recovery heartbeat in addition to normal event-driven publication.
This protects a valid daily edition from being stranded by a transient runner,
browser, artifact-upload, or Pages failure until the following day. Publication
gates remain fail-closed; periodic retry does not bypass them.

## Reliability maturity

`OPERATIONAL` means the real production path has now completed successfully and is
actively monitored. It does **not** mean long-term reliability has already been
proven statistically. That stronger claim requires repeated unattended daily
cycles. Production health and the live oracles remain responsible for accumulating
that evidence and detecting regressions.

The next product milestone is therefore **boring repeated success**: each day's
material research should appear on the public newspaper within the freshness SLO,
without routine human repair.
