# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f732144f0c27c4141382feff**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-18T16:17:47Z`
- Edition: `2026-10-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4695 routes; SHA-256 `1f9a0573cac5448ea8d186d099b13c3f74d362817ee8d3edaa124d8758cb9336`
- Route locales: en=1565, es-419=1565, zh-Hans=1565
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=111, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2244, search=3, status=3, story=1749, subscribe=15, topic=501
- Story routes: 1749 for 583 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `46e5de8b83fcae5eb9d2756267cc91d32f2386f8fb3528a66b0c1b67efc99ce2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c3fa9cd8b07cdb8e84354477d98893bdfa8161cac3416088a34463af6188d877`
- Candidate tree: 16860 files, including 1758 local story-media files; SHA-256 `34f831120d0cb649924cc001ce4de0e5de24186f4835edac53f7566a4213ba2d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
