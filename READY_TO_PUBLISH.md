# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-1477674681ead4f9816a56a9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T22:50:34Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1323 routes; SHA-256 `53763dcefa10f850b2a9231fd5bb82fa5d9a86f1a1925d6da28c241c5137c8e1`
- Route locales: en=441, es-419=441, zh-Hans=441
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=621, search=3, status=3, story=402, subscribe=3, topic=141
- Story routes: 402 for 134 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ee1b1939e7ca70d4472be8fcf8dce51767be3f460ade5034abb20a5e269b7cf1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7424c9222630860729a1b8b159113c8f245ae663d26c74024796fe6a4bf8e32c`
- Candidate tree: 4695 files, including 411 local story-media files; SHA-256 `53fb5c4432f679d5e9178a8962b85838030d4bf274f9efa9fb4a68e2cd0ce146`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
