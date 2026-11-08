# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c65d4e1ccdd0feb9360b61af**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T20:33:33Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7125 routes; SHA-256 `29e3b3a05836ceb9914e14a0d4c1fbb94face7372ef32928ef1bca5e9a58f37f`
- Route locales: en=2375, es-419=2375, zh-Hans=2375
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2775, subscribe=12, topic=753, topics=3
- Story routes: 2775 for 925 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3cf47f822b3eab6ac9796c48fbb2a43d5160b51a1dd823a5dc20c75c28b49e0a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b875e3b5b7ddfdce2df54091f91386483cba2399015cb73c98d88108ec677e9b`
- Candidate tree: 26105 files, including 2790 local story-media files; SHA-256 `32f0e70fe3b17dbfd58143d77c9d62f87d6a703d1450b6433c1414c1d0f09196`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
