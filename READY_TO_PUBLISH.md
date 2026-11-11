# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6bfe279b3132ce6e282daecf**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T03:34:24Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7299 routes; SHA-256 `882850097b7d25059deb43822071f1a8b625dad83d50afe4b985e568f65ab5d8`
- Route locales: en=2433, es-419=2433, zh-Hans=2433
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3357, search=3, status=3, story=2856, subscribe=12, topic=771, topics=3
- Story routes: 2856 for 952 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8494c3ffa1112bd317830c2f9355d794f35bb9bff355ea07edd4c94baab71b2f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `59b41ee5658271b2f33655b18fbd1e13bd3b16f0e9a5cf96b19f05d004fe77b6`
- Candidate tree: 26807 files, including 2871 local story-media files; SHA-256 `6654ac292458f9b4431a9ffd0258317388c11b7d705e1992dc5d936a104fcd90`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
