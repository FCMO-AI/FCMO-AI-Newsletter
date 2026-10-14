# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c6cd19dbbfbb87ef1840c1aa**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T00:58:13Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3303 routes; SHA-256 `2cefe6e8461059297a2c2e73f858107395e5ec9f0784084b69354e32b2c3cb29`
- Route locales: en=1101, es-419=1101, zh-Hans=1101
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1605, search=3, status=3, story=1167, subscribe=15, topic=345
- Story routes: 1167 for 389 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `bf8ff6058bff3faea3ae70b871f4fd43c90df228ba732d79aca0e62147faf659`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `fe1ad770bd765437175bb52fc4cefc21e234c536e950015318478d8e61c9d1a0`
- Candidate tree: 11739 files, including 1176 local story-media files; SHA-256 `5896107a957c5d4ae9fbd068c65c25f9f6294b6d03570afa56dd4bb57e0ae1ac`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
