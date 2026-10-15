# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ca6e6ce48cf8d25175e07425**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T05:05:13Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3762 routes; SHA-256 `51546af11f32f37df3125b1536efa27978ad4bf5ae68ea88940686af4ea647b5`
- Route locales: en=1254, es-419=1254, zh-Hans=1254
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1824, search=3, status=3, story=1368, subscribe=15, topic=381
- Story routes: 1368 for 456 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `64acc0ffef5e89687138a6bcd025e32266987b371f4faa07253543752bdce28f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5697fec60d9617a9caa2eecc55dd2299bff700d853de96cc6ff34f62db328303`
- Candidate tree: 13479 files, including 1377 local story-media files; SHA-256 `4b225c293556e2378e5da50c865a0a75bf5cb673a43f9e55d278bb662bf55b7b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
