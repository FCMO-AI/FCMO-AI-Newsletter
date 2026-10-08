# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-063bc171436eec4b6f46abae**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T21:49:42Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1290 routes; SHA-256 `8005616437c30a6f7d1743fbd0e9a8752198dd836b0befcbc9e6f09ce42f9b54`
- Route locales: en=430, es-419=430, zh-Hans=430
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=606, search=3, status=3, story=390, subscribe=3, topic=135
- Story routes: 390 for 130 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `2c78b4b9ad09e2130702b97e0edb1d132f95c68406630dfd578fa5b52346e050`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d0317885e74d8fbfc91465c7ecd58de8b9009684f3d118eee6b26847625102d6`
- Candidate tree: 4579 files, including 399 local story-media files; SHA-256 `c77e0f2ca04584d97886600c4b2d9b80a863c7f64f8d83c892db86809582689f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
