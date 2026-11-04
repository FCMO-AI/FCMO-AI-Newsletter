# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5da233005890794ae1b3f29d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-04T20:36:18Z`
- Edition: `2026-11-04` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6852 routes; SHA-256 `0a6b7436542986b0874405acfc08925e1e4390e75f2f6d0291c092cdc0bdbab0`
- Route locales: en=2284, es-419=2284, zh-Hans=2284
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=162, feeds=3, landing=3, legal=9, letters=3, method=3, org=3192, search=3, status=3, story=2652, subscribe=12, topic=717
- Story routes: 2652 for 884 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1fbbb7e0eb4d9d0065326d70e8ad1eec47a6c6a1f2a029d0031ce5e210b3a244`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7bd1a87a888b834b135d1e76179b0d7a456e68e78b00fb990913584a9670a229`
- Candidate tree: 25017 files, including 2667 local story-media files; SHA-256 `957ae8943d9dcad602d7d965ad3ba2bc5e7bd083d02a8d576e2a4919977e6823`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
