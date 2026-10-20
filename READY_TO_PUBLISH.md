# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eb37f42cdb8fa697d3a423eb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T14:11:01Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4881 routes; SHA-256 `da67e3b343d9737e0ed0b08812c0dbdc75217dfcf5ad66629779076631f4d4a4`
- Route locales: en=1627, es-419=1627, zh-Hans=1627
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=12, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2313, search=3, status=3, story=1836, subscribe=15, topic=522
- Story routes: 1836 for 612 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `69264e201bf0a4ff17670ecc10f5b62311f3c289d33107916797a98820ae1dfb`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5623e33177e8b60a46a8fb366d6e9a4da4820cac35490422349b0c35bc40e5a3`
- Candidate tree: 17611 files, including 1848 local story-media files; SHA-256 `18f486f8df22d97124b255d0f25b15a51c329b64d0bed9a94f9bbec3f8485fb5`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
