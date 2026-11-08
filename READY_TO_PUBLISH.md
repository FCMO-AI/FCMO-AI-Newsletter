# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-246eae8d164c5a8861f1fb32**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T04:33:47Z`
- Edition: `2026-11-07` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7119 routes; SHA-256 `b97a31fff9b03a3aba2930c653c2daceabd936d869bdf751e93d86323f96694c`
- Route locales: en=2373, es-419=2373, zh-Hans=2373
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=171, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2772, subscribe=12, topic=753, topics=3
- Story routes: 2772 for 924 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0d27f9e74bfc57a9add9b5e1705319e599d394c242de471e5ddb00d5104901d4`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3484213bcda909f7933d4cb5076ce9a110d04d94f123130323a9cd7ea0b4792b`
- Candidate tree: 26074 files, including 2787 local story-media files; SHA-256 `2284201866062398d9932f2eb0807a834601254398a89194bbe7dd3fd9c03123`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
