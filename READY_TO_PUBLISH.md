# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-282102ea06e02d551d2af3bb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T22:57:45Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3234 routes; SHA-256 `9f4c74f763a24c9af6b41be278176bce0fe54da8378ac786ac33751bf9342305`
- Route locales: en=1078, es-419=1078, zh-Hans=1078
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1563, search=3, status=3, story=1146, subscribe=15, topic=339
- Story routes: 1146 for 382 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c81b3d76611d2289a0e732b41385d878b87ef796dd37f978395b48940826a5c3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `607a50ed9810aab163e6b43990ee2c16475d8a74f4948307dac5ce37a67301aa`
- Candidate tree: 11531 files, including 1155 local story-media files; SHA-256 `c65702bf7e72d111ada69c1edfa306b2c3ae1f283a503eb6c01004894c4211c9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
