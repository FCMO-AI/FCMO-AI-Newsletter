# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c680d8c6cc81a579de961bef**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T06:09:28Z`
- Edition: `2026-10-22` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5130 routes; SHA-256 `efea7a3eb1428c1513f2ed21bb8ef5dbd800c46d524719952f21e82a01f4c976`
- Route locales: en=1710, es-419=1710, zh-Hans=1710
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2427, search=3, status=3, story=1932, subscribe=15, topic=525
- Story routes: 1932 for 644 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b86e20fc09fc2468209a2847d6712c43e35533a6aa949fd69dbd9ba1a1f5b592`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `fcecd975ce0bb1da653cbae39afa27fbd1be926e673ba21d25274c02f7519f83`
- Candidate tree: 18481 files, including 1944 local story-media files; SHA-256 `35b4eb645f9deb1a7bedba6244e4e69e561ad8de02e91e972ccd1a6c70997c2f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
