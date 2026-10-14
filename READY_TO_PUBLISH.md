# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-667f6e337561580bf62c6ae1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T17:02:30Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3600 routes; SHA-256 `809892e7d5594628ea9460d68de089d347cdf45e841f903b09dea53a46d57c00`
- Route locales: en=1200, es-419=1200, zh-Hans=1200
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1740, search=3, status=3, story=1299, subscribe=15, topic=372
- Story routes: 1299 for 433 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0ed7dac34c50fdea78bdd808736c82d8e28b6a0d698a5fbe6da7dfb3031aa436`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ea81db05077104515904e1ae14f8db820a042b1bb3814fe1574f98dbd67ae428`
- Candidate tree: 12890 files, including 1308 local story-media files; SHA-256 `1008cc7ed04ba59ebec0e45ac648009ec25d484e060ed11d88d90f01ff4caa65`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
