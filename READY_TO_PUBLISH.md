# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-db703c78bc9edf12fc14dc0c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T04:56:57Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2541 routes; SHA-256 `e0cc4ff74b15589552836fe29a696ac6d6a48afa7569d9d49ea5d4398c0084ba`
- Route locales: en=847, es-419=847, zh-Hans=847
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1284, search=3, status=3, story=837, subscribe=15, topic=240
- Story routes: 837 for 279 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7b9ebed836d6740fdea420d4248639c3a10f949950c2e8d0dd410f876570b75d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `53e44d4e675782b15ed6bd3a7028c2ac77c090bdb5e8091a88de454adae359f1`
- Candidate tree: 8869 files, including 846 local story-media files; SHA-256 `df1cab709d86a87341c33f2381b5735f1fcb57e9d2fe1a3ef01d8aed4c935b50`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
