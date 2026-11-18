# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-734001ab08c7d5bf0a9353a9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-18T11:46:02Z`
- Edition: `2026-11-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7500 routes; SHA-256 `804853c7d8ce24b36502401c6436d5f33aa33ed2c59fa4975927807de456b0b0`
- Route locales: en=2500, es-419=2500, zh-Hans=2500
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=195, feeds=3, landing=3, legal=9, letters=3, method=3, org=3420, search=3, status=3, story=2952, subscribe=12, topic=795, topics=3
- Story routes: 2952 for 984 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c9aa6bff84d4bfda19fd871faad5a755c5aa581b7d49b785c914951d1c0b43e5`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e817bb5edcb26aa194d5d88b2d6423b5eae950c269f2875ee843084559b40358`
- Candidate tree: 27663 files, including 2967 local story-media files; SHA-256 `c4927dcf2c3899b3b1bb229f7ba6ecbcf35d009cd4dc6e2ba35b366666df1610`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
