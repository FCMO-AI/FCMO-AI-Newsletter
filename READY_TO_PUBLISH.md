# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-853810a78042db3bebb21e6f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T04:13:18Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5106 routes; SHA-256 `c29544bd9770daf1581e5a7384dbfec6255b15d8db42178f9fac134492a38a04`
- Route locales: en=1702, es-419=1702, zh-Hans=1702
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2412, search=3, status=3, story=1923, subscribe=15, topic=525
- Story routes: 1923 for 641 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0ed3c657bd5b5ea4dcab540715bc3776c960723859125ae7037ef7a86344dfd4`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `1840dcac285f502e5a4bccd802e204969c63146f4dd6073dcf0e817561a289e8`
- Candidate tree: 18403 files, including 1935 local story-media files; SHA-256 `fc268720a9239de17a9cb6b2d49bffb396e097f3a787cb50021e3ce302516d19`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
