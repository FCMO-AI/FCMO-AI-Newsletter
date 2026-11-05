# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-8a95feabd1b0cb5ffabdb284**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-05T02:34:54Z`
- Edition: `2026-11-04` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6894 routes; SHA-256 `ece54acb7b4e168f9460bc81cc4c3b7d3ca62619779f01cf2c764442afe781f8`
- Route locales: en=2298, es-419=2298, zh-Hans=2298
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=162, feeds=3, landing=3, legal=9, letters=3, method=3, org=3213, search=3, status=3, story=2667, subscribe=12, topic=723
- Story routes: 2667 for 889 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d04d365d10e52eb00641ab2a197945381f23be0f4cb01af67995c2afbb5f41c9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `622a4c8c6e56639214bb7652452e70dd52ca5c4baa158df0fef3901b0749f6c5`
- Candidate tree: 25160 files, including 2682 local story-media files; SHA-256 `5416056142f008a6c6cbc84896b21c07967ecfb27fc04a94351a0967a416a605`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
