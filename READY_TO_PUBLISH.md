# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5cc391e7ee3fbb82b6440e4d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-13T01:51:03Z`
- Edition: `2026-11-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7419 routes; SHA-256 `0d52e569f32723d4af644eeb75a28f20a9ef07f1fee6674c48986cfbd3ebbfb0`
- Route locales: en=2473, es-419=2473, zh-Hans=2473
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=186, feeds=3, landing=3, legal=9, letters=3, method=3, org=3399, search=3, status=3, story=2910, subscribe=12, topic=786, topics=3
- Story routes: 2910 for 970 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `297aff331da775b2b35c92e8a57b64daffc7947e80293a253b44363567dd1cbb`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `83b030501a37ba74052257364a6f07db42b9970a6c75c7d5f827cea2c57079a7`
- Candidate tree: 27296 files, including 2925 local story-media files; SHA-256 `3ab8ec9f49a98653d913c80e67ff7c5fc1f01c9e8fc77649362199da9f47dc94`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
