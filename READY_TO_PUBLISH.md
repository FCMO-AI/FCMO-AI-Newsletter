# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4c8519b32095fc3515f7d3da**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T20:42:36Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7356 routes; SHA-256 `e5cef22bb37853fd54ab4be041e80c42691f303eeabc675534196477890b220d`
- Route locales: en=2452, es-419=2452, zh-Hans=2452
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3378, search=3, status=3, story=2880, subscribe=12, topic=777, topics=3
- Story routes: 2880 for 960 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `40c12482b87418d1cf58e62a7e095298ea889d6899b68dcd4c1a85a5739fc85d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e2a56c40ca6bad9b9630e9d7abe1616fa559e19b61a797cf1df3a99a22895543`
- Candidate tree: 27034 files, including 2895 local story-media files; SHA-256 `1d7be60886ab7f78b6db9820a5162dbc6fae119d706b6eb96a44e07cedbc05d3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
