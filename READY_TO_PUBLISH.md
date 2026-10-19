# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ba7a23900b7cc97d72d744ed**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-19T02:12:59Z`
- Edition: `2026-10-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4740 routes; SHA-256 `5e75a33e8313b90e2fbe5cbd70929939e5f3d5d73b657bf49319d62ad8418c17`
- Route locales: en=1580, es-419=1580, zh-Hans=1580
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=111, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2268, search=3, status=3, story=1764, subscribe=15, topic=507
- Story routes: 1764 for 588 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `e9780d7b4f29176d5453834545ed1a68183a542129a0f3909c0762cdc62cf24d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8cfb43fef78d5c30539f4ca4f9c80eb7e305f4123b77792917dfd14ddcb071ee`
- Candidate tree: 17010 files, including 1773 local story-media files; SHA-256 `60142bc1929044640dd4bb4f5182a60fa6927215b52f6c3991b758ea6732a47e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
