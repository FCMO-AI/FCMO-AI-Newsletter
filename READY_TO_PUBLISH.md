# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-0f50a33fa834f454c06d3ecb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T00:21:05Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5394 routes; SHA-256 `666077cafab75faf81e1b85251596c72cfe24f66e6912d7177c433266cfa5d71`
- Route locales: en=1798, es-419=1798, zh-Hans=1798
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=126, feeds=3, landing=3, legal=9, method=3, org=2574, search=3, status=3, story=2040, subscribe=12, topic=546
- Story routes: 2040 for 680 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `aae5d33680cfa448d1e8c6202eb72da0883f9f7610dad5aff4480ccd8518fcd1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2f2df13270d4af4d0585e215740bd107ca37879cdd7cbdea06cef8f83a65ef21`
- Candidate tree: 19487 files, including 2052 local story-media files; SHA-256 `11b523b526696e5311402a6df62df8051d36f0404685b0ef32e7ca11f5db45b6`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
