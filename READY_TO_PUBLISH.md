# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f342c6bc4d91f5b31733a4d5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T19:34:48Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6591 routes; SHA-256 `ddfc5fa2a52d4427c8b14641a4c4d40d1a7f7f02f717efbdea29a39fab124585`
- Route locales: en=2197, es-419=2197, zh-Hans=2197
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3072, search=3, status=3, story=2544, subscribe=12, topic=693
- Story routes: 2544 for 848 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `2d578101928180d250253fc02e6bba7dc1533c5fca7b05ebefc5a9bad2021ce2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5b87abd4284b2210c4c95027dddbcb1f9bf829daa406039aa6464d1652202085`
- Candidate tree: 24044 files, including 2559 local story-media files; SHA-256 `c2566c12cc69dee54f58345e9ded0a5a25ee9d5dfbc1ab4a221ecde884fe72c4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
