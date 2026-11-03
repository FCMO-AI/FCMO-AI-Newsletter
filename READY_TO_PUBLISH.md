# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b461407a5ec2c71e4b44c80c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-03T08:46:56Z`
- Edition: `2026-11-03` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6681 routes; SHA-256 `612480247ffdb5a4eaa3e9711f7de07ecafe1893feb7e237b31397faea8ef6c0`
- Route locales: en=2227, es-419=2227, zh-Hans=2227
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=159, feeds=3, landing=3, legal=9, letters=3, method=3, org=3114, search=3, status=3, story=2580, subscribe=12, topic=702
- Story routes: 2580 for 860 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7b356bb8842f014c64d8b4c25478b469e6e3e0c52f770680f1e5f0c3129d1e27`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `1c8231e23f3111243279d3d1b5bf1cac81ed141a02d6ed1d0521b16462ee8468`
- Candidate tree: 24368 files, including 2595 local story-media files; SHA-256 `4907de4f6ececada659a52d094ca130755b3c97cdaea8d6551fad168062fbbfe`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
