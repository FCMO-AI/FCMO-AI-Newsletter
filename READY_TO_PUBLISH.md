# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-1729bd8b2fae94cbb937934a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-18T09:43:08Z`
- Edition: `2026-11-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7491 routes; SHA-256 `319f4d58c78082f770139b709ca787d3d7afe89fd92b74baf013199dc4a715d9`
- Route locales: en=2497, es-419=2497, zh-Hans=2497
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=195, feeds=3, landing=3, legal=9, letters=3, method=3, org=3420, search=3, status=3, story=2946, subscribe=12, topic=792, topics=3
- Story routes: 2946 for 982 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7c2ba3491b7d8218d306003bfa5d3b40f95182f2bff7a83aaf61c9074877e7cf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `fce2d7efffcd8cc15a8689de443a7046847fa24335536789be5a0fe94a82c0df`
- Candidate tree: 27620 files, including 2961 local story-media files; SHA-256 `80f7921d296ae7c5d0a1a8311152c3ab7d044fb2479a3ec92b85921219d180c9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
