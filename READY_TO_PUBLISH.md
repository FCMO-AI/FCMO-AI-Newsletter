# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c0731daa041eb9680c47b95f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T12:18:30Z`
- Edition: `2026-10-25` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 5463 routes; SHA-256 `0648a9ac44370bb1dca9e22354a0f8af7daf880b53254845911112eb7677e640`
- Route locales: en=1821, es-419=1821, zh-Hans=1821
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=129, feeds=3, landing=3, legal=9, method=3, org=2610, search=3, status=3, story=2061, subscribe=12, topic=555
- Story routes: 2061 for 687 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7b12e06feaa5a31068298984166de220045eb46a6a4318447811dbab638f5e14`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7e1f53f10ace8b2fade6b20f5717a4f47cb5b71b48f1d9510f57ccfb26d702bd`
- Candidate tree: 19711 files, including 2073 local story-media files; SHA-256 `ff5351fa11b97b4df323da80fde3f54f76ba1ae4f4d5dce1d2305b74d50c7b90`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
