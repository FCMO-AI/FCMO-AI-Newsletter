# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-355feb275130a3edae39bc32**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T18:58:53Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3165 routes; SHA-256 `b6d6498fcd8cc63b07fc9baac4a81ec6bad2313f75889d1bbaeb8a63abbb8bd2`
- Route locales: en=1055, es-419=1055, zh-Hans=1055
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1545, search=3, status=3, story=1110, subscribe=15, topic=324
- Story routes: 1110 for 370 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `e75d2418ad74b82326a0cd40b446741ed49f51439a826de3d25cda3e15a09be9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `933aab6065f1fc06686d149c3ecd0a6eb70fa8ebd7f631106e097d6814f69d47`
- Candidate tree: 11239 files, including 1119 local story-media files; SHA-256 `c5a8a1fdd4cca634bd89da6659753563b9e18c2664bda0b623bb16c4d9b34d38`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
