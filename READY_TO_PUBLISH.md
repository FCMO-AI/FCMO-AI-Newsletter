# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b4899f2beb4b7b9ef5220e33**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T15:01:49Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3069 routes; SHA-256 `551f2800eddf647cf4c8a27a972c4cc6ce26c316d3b10c3e64aaee9927451c9f`
- Route locales: en=1023, es-419=1023, zh-Hans=1023
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1509, search=3, status=3, story=1065, subscribe=15, topic=309
- Story routes: 1065 for 355 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `cb3d2e5b9573397473e5d3f2ba5df992f42848cd0917a0c11843993f5f3aa769`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6240dab1b312ac1469e03d6c8a3fc7df05e52c8ac38d10e78f93a6a63d56a979`
- Candidate tree: 10859 files, including 1074 local story-media files; SHA-256 `220a89ae8b61430b7e45cfb4d462ad52081d4bc74b3870582bb0f16655e6fd25`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
