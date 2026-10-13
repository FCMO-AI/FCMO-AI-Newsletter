# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b4135a0078fbb262d63b73a9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T10:57:51Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2991 routes; SHA-256 `9b5507dbd45a2371edc9b9587c0a4524912b6804f95fa4f531b211a0e81c5be2`
- Route locales: en=997, es-419=997, zh-Hans=997
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1470, search=3, status=3, story=1032, subscribe=15, topic=303
- Story routes: 1032 for 344 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `e3bacc8d628f345060dc2cec9de3fcec878cc8b0945e652319a1321fa623a48f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `db52baab05ea27b732b7e68b6a754a791bbf0b378ba5e30d27b4a71017cc87c4`
- Candidate tree: 10579 files, including 1041 local story-media files; SHA-256 `4ced09c325d91ade86e28ca73ebd029949e1ab7a223d91d780900cbc3f23f276`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
