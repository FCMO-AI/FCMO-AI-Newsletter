# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4fd865f6dc4b6bf83a6df96d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T04:59:48Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3372 routes; SHA-256 `00fca8ee8bcca1d5a5650ca2adfb4070fe9e048e755dae4f803d62fff2e483c7`
- Route locales: en=1124, es-419=1124, zh-Hans=1124
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1641, search=3, status=3, story=1197, subscribe=15, topic=348
- Story routes: 1197 for 399 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `93dd62dd2a503761bea816de1a9a140514f120f1be4c7f67be8ffc38e6a56f8a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7d5ec429efce37aa9a721251900c6892ca0b5e39f3c28207e78ca549fef958cb`
- Candidate tree: 11997 files, including 1206 local story-media files; SHA-256 `9f2681d1752c52395119a8753fba9acfd5d9d68544b01ed95b51d0964c9f3e4e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
