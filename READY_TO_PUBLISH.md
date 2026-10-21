# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-316a91f3dea7ae383cdc27ca**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T02:12:40Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4956 routes; SHA-256 `6b68a8f07a36ca0ea93fc05ea98f55f92c8936a7e15ef7c4f52727322d1fc1f0`
- Route locales: en=1652, es-419=1652, zh-Hans=1652
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2352, search=3, status=3, story=1872, subscribe=15, topic=525
- Story routes: 1872 for 624 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0d05ce6fa7163e177d238731c814ec512c65fd049b1dfbc0c870c5aa4462ab54`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `a1159c3c92bb0e8f4fe1f3043c7726e1e4ee8c35dd5e9131264d9fa94d333d01`
- Candidate tree: 17915 files, including 1881 local story-media files; SHA-256 `cb13848238842443e35d7fe4c8b49cd4366807cb7d172fb19fb8908fa1216b1e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
