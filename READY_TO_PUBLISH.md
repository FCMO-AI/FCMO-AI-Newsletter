# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-441740a2cb012f75c3b47ac7**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T01:33:33Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6009 routes; SHA-256 `6ff4a87a4de2b73eb958d5cf61b35cdfd161e6d1f42016194e8ad84c3e5a22be`
- Route locales: en=2003, es-419=2003, zh-Hans=2003
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2814, search=3, status=3, story=2304, subscribe=12, topic=630
- Story routes: 2304 for 768 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c8ae508e4a2e740f2831b24e0493a917dd36122d017903a5593a222a026f4533`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `746563374f26976d15a67ae6b4824c02de59a9f2d340c3627473268e164c01b5`
- Candidate tree: 21831 files, including 2319 local story-media files; SHA-256 `a24c7e8abe3e5c9a60ecd9b481f79aed67d16c43d498ab2de90a59e8b07ebb4c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
