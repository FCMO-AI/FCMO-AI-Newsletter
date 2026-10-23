# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3e410d00cd3ba2d5d7b9bcdf**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T17:14:32Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5325 routes; SHA-256 `7f9d02fee2c3f37b42b09335ad662eb18c1f4e7b3ccb009199023a69d88899fd`
- Route locales: en=1775, es-419=1775, zh-Hans=1775
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2532, search=3, status=3, story=2007, subscribe=15, topic=537
- Story routes: 2007 for 669 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3996ecf1944ab72a90156883c67566f4e0b4aedc1fde2fcb01c71c5fb2565ea8`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d3f7cab3cc59cd75be512edd897a8ae834f1163cb18b2a975858b4ef7372f79b`
- Candidate tree: 19188 files, including 2019 local story-media files; SHA-256 `f7213ff218dbb2d55c5f9e1fc3c3a24d8f1bca8bcb02e9e55b5c1a5dc8c6cd28`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
