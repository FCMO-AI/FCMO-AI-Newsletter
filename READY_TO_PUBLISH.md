# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f65b13e985154885c4879f25**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T13:13:36Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5043 routes; SHA-256 `16244334e5c1f9cd3e5f7fc253ca85bbd5d7e796616ffd96ba51a82596ba9a0e`
- Route locales: en=1681, es-419=1681, zh-Hans=1681
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=9, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2379, search=3, status=3, story=1899, subscribe=15, topic=525
- Story routes: 1899 for 633 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0827bac88f0f97cab4a254d6505c90fb0f9e0720aec5495dc96682bc0b12f9a2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5e366e85ae0f663cc9fd12e96800bc41e2a43e68162a1c9a27ab5da1d9845aef`
- Candidate tree: 18167 files, including 1908 local story-media files; SHA-256 `f855944b8f70f61b86f2b8e98e6de62cee18f39b55f1111aac194159b381bb1c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
