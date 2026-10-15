# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5517d3f51642b54189d9af83**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T00:01:38Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3705 routes; SHA-256 `0cc3249f7dc5a51e96affb1ffc413ce87a09445780908e96ac34866e7a9b7a3a`
- Route locales: en=1235, es-419=1235, zh-Hans=1235
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1797, search=3, status=3, story=1344, subscribe=15, topic=375
- Story routes: 1344 for 448 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c58ff2d49e137c797fa03320db7d858e75ba70fe66cbf5a1c120eec4e5c1d49c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cc8128f37d5931680bea98606ab284b87abaa57b9c3796e137c73565e9126846`
- Candidate tree: 13267 files, including 1353 local story-media files; SHA-256 `f1b02d4a41de90f99cddbc6d418d56c853a304245e792569a41e8e8665c0dad6`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
