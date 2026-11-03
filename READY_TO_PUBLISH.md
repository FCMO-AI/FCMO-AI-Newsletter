# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-afaa01eeb355b69f2730774d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-03T18:35:12Z`
- Edition: `2026-11-03` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6741 routes; SHA-256 `e7e2fbae76286e4a1561bb7e2c2bd334af47b018b5d63f66e3e705f75995688e`
- Route locales: en=2247, es-419=2247, zh-Hans=2247
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=159, feeds=3, landing=3, legal=9, letters=3, method=3, org=3141, search=3, status=3, story=2610, subscribe=12, topic=702
- Story routes: 2610 for 870 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `f33233989047fb95a385087b129531a44ff8e42eb3821480d8571598acdbd28c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8a30950d616d126907d65908b14cac963e12b183834fd89780141194bf6740c2`
- Candidate tree: 24624 files, including 2625 local story-media files; SHA-256 `891f8df114a56af0c5224a6568002f6dc2333b0a1fae78b0c8f3a9ad66557ca9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
