# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-677c10ab70899c7f77f287a6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-16T04:46:02Z`
- Edition: `2026-11-17` (`QUIET`)

## Final route/data manifest

- `data/routes.json`: 7479 routes; SHA-256 `d197e090ee9ad8797f022eed3ac9496a3c49b620c0344e81c6575de4a306bea1`
- Route locales: en=2493, es-419=2493, zh-Hans=2493
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=192, feeds=3, landing=3, legal=9, letters=3, method=3, org=3420, search=3, status=3, story=2940, subscribe=12, topic=789, topics=3
- Story routes: 2940 for 980 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `899160b2b9680d0e2c211eab040770cd46cdbc3b42ce211b2bd5d2d39181fa75`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e64bd3d3b121d0b2667b68c65644421db18ad993b23d9165531295fd684f9bfc`
- Candidate tree: 27564 files, including 2955 local story-media files; SHA-256 `46e6536b982e8d19da85fd487c34b7b1e920e2cdf3dc4430ea94eba1afc51777`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
