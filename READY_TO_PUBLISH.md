# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-88ed127d3fba533d22bab3af**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-06T03:00:49Z`
- Edition: `2026-10-05` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 558 routes; SHA-256 `42c3c642c3af79c0f985d577840a0771114fb9a219e9d280e3ec5c342976396d`
- Route locales: en=186, es-419=186, zh-Hans=186
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=72, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=228, search=3, status=3, story=138, subscribe=3, topic=42
- Story routes: 138 for 46 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `422e88048a18845a2c8293631b55c63b9fc9a05f20fda30c361c5f816e4ebfb2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3ac0885eb692545797429e6c5c0dc3061a5061a4b187dd1224b23fee32af8784`
- Candidate tree: 2075 files, including 147 local story-media files; SHA-256 `a3dc436adaee1caadc8c76dc4b78061e21c6f7cb24f16abe37171f195539f448`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
