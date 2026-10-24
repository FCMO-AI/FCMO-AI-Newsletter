# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5b7d857e7bd672c792b16ce1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T03:32:40Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5415 routes; SHA-256 `5b605d9624e4874ee06248be4225f173eb78644f73a7e23bf72a02ea37b3ee9f`
- Route locales: en=1805, es-419=1805, zh-Hans=1805
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=126, feeds=3, landing=3, legal=9, method=3, org=2586, search=3, status=3, story=2049, subscribe=12, topic=546
- Story routes: 2049 for 683 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0e18bbcfc9d7915a95973b4c8aaa4329afcc3b97c2e008758a6a957f9c11c947`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7eeb24aa6e9f5cc5f49f34ecbab88b9147402b24c9f8f27553c4a3451795229c`
- Candidate tree: 19574 files, including 2061 local story-media files; SHA-256 `691bef446e742db4baf6413dd0ac8ad52415621485fc9625bd121efc9db32d1e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
