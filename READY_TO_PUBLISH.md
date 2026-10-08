# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6564e3beac49ced8c8009cc4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T19:48:49Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1206 routes; SHA-256 `dfc78afcf0c6d66aaaf1b76659d26cb767650d428667cbabdcc09b76b0cc4827`
- Route locales: en=402, es-419=402, zh-Hans=402
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=570, search=3, status=3, story=360, subscribe=3, topic=117
- Story routes: 360 for 120 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a426b3d345baa53f77f040c73fdf3a346ed25c65e9d29a3d1e6a2fa9e1e48c39`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `018453e9565f9023d354856e0824bff2178c87ff8da3d87b8796955ce57fda84`
- Candidate tree: 4294 files, including 369 local story-media files; SHA-256 `3c2e5e32d61bf745fec2b75debc7426e876261fe092419f3ad7b482cf45d304b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
