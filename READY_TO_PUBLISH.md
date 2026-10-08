# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7af35e2c501c10a8cc258b14**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T23:49:57Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1350 routes; SHA-256 `7f3c11a4ab6022b4747d358bcf775e9fc77fe9290251dd3ac0e80ff65bf5e2fe`
- Route locales: en=450, es-419=450, zh-Hans=450
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=633, search=3, status=3, story=414, subscribe=3, topic=144
- Story routes: 414 for 138 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b4c969cbd313576933a921efbcf54b564b210402597b332d047c1f3b9e4af354`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `92d4568bb64db5ba081b320a7cc356687563ab7028ccdfb6dc1055491c496d06`
- Candidate tree: 4803 files, including 423 local story-media files; SHA-256 `0705bdacdfadfe85451b0bae1219b6a115367d583d6fa9282294fab6ef856950`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
