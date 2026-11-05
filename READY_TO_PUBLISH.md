# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d3a08d5ba9d3998395b21082**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-05T00:37:52Z`
- Edition: `2026-11-04` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6879 routes; SHA-256 `288295e5fda37e199df7c6b67ff91d22c2dec4ae81e63e169fe63a47e4086e50`
- Route locales: en=2293, es-419=2293, zh-Hans=2293
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=162, feeds=3, landing=3, legal=9, letters=3, method=3, org=3207, search=3, status=3, story=2661, subscribe=12, topic=720
- Story routes: 2661 for 887 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b9f18341b1758244a54f14e22855f869f1a301f87df7e0aa187c4025c2543032`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5ef3075e00db985d81217c961c77f88b144e6654572c115a6796a624f1264976`
- Candidate tree: 25105 files, including 2676 local story-media files; SHA-256 `db9472c12b24f70a986fcf466bedadf925e106746cab52746e1444b9a3ec1c58`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
