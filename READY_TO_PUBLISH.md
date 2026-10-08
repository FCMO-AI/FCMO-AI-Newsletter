# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-13d88f73050169432f61d24a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T17:48:57Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1152 routes; SHA-256 `5f5e0514465e5e77bd3ef8a0dadd8861766e6e6105a5f064c0776c95b5e1d6e6`
- Route locales: en=384, es-419=384, zh-Hans=384
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=546, search=3, status=3, story=336, subscribe=3, topic=111
- Story routes: 336 for 112 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `f8a387165c816967a1f30a0796e1119f6444a8641382866e72ff8cdcb3cd1d1a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3c81020041f40f46e526236df77147d50d2ee8576e9dc84e9e8770de5b6e73dc`
- Candidate tree: 4082 files, including 345 local story-media files; SHA-256 `ea12e10fc70968f49a68a123ba07eb75a25193b8a05496fc49aba963ed8306fb`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
