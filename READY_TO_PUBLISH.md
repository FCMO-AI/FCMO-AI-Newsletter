# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-bc8677958e206d1a202d8c47**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T13:02:16Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3528 routes; SHA-256 `3286607cb843964dcc2201f3f3653780b5fa45e9ba43e0b341bd8a1f64351e2b`
- Route locales: en=1176, es-419=1176, zh-Hans=1176
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1704, search=3, status=3, story=1272, subscribe=15, topic=363
- Story routes: 1272 for 424 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `dea3d8e53037cb36536fa9f3190dd6efb424b8389aca745257528355ce8122cf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c07d123b6260074e93822d688faea9a4ef7c0a1c776bd75de1d302f0d9a920b4`
- Candidate tree: 12647 files, including 1281 local story-media files; SHA-256 `9d3efaf6b586c7b0730755d5bcff123094760286b9c029b789c4687d753f1c13`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
