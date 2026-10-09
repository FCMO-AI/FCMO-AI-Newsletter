# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f6e17ab974211e52c0e1baf1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T02:51:23Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1482 routes; SHA-256 `4cf104f89df91ba4febdaeb80f7ff377eef191f3a1a4e775407f76c138e00dcc`
- Route locales: en=494, es-419=494, zh-Hans=494
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=717, search=3, status=3, story=450, subscribe=3, topic=156
- Story routes: 450 for 150 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5fbe8edd47ed5dd829be5cd3b68ee2dc1704f172fe6ccd2ed675454e7938bc9d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b03f4575a9a94dfae6081fb857b772404f0c05623e739b3cf0e7336ff59b26eb`
- Candidate tree: 5195 files, including 459 local story-media files; SHA-256 `0a9210bb0b096477548eecb67718b9a3c63ae41fb3b4a0e9de139a287218e819`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
