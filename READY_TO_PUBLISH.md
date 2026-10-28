# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7a22030bde194ee70cbea6bd**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T22:59:28Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5988 routes; SHA-256 `8cfad81bb2aa9a651e42044d98aeb1bf11621ab1b13b84a9fc86ff92edf3fbea`
- Route locales: en=1996, es-419=1996, zh-Hans=1996
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2802, search=3, status=3, story=2298, subscribe=12, topic=627
- Story routes: 2298 for 766 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `469a9bba2a2831ad2d0a6baab0c06467503854594dc8a6cbdf696b6014966b02`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d6581d3f87f5264189a653cd3ca9045e8473f5851291c044aa2263e80e6ef54e`
- Candidate tree: 21768 files, including 2313 local story-media files; SHA-256 `383f6c5d1ae145b94d99dbf66c169a85d383e342cd61725ea57df4b699c8de6e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
