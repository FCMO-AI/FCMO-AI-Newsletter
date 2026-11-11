# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4387777289506bed7dd0afcb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T13:43:02Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7341 routes; SHA-256 `3afef0825e885b128310a7c51215add5f63baaff7d393076bcb77a491f4d976b`
- Route locales: en=2447, es-419=2447, zh-Hans=2447
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3369, search=3, status=3, story=2874, subscribe=12, topic=777, topics=3
- Story routes: 2874 for 958 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ce3e78ef09c89ec2e770cda9afa4329ce0889b332022bd26778b1dd7b8cb392c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2962b9f703c403a301ef54cd0a0196ee2ae924137d862b1ad9cdd914e65e11ee`
- Candidate tree: 26975 files, including 2889 local story-media files; SHA-256 `8eb7ed85568af6b4e58d8c8f06a183deca0b66530f50180c3a16ef75983bc061`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
