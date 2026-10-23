# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4aadfe5bf6240fecebcc0597**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T18:17:36Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5340 routes; SHA-256 `5513023e68051afb4d76b4f978f6adb1df5b7a0336b79c1b6a8e56635803cf49`
- Route locales: en=1780, es-419=1780, zh-Hans=1780
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2541, search=3, status=3, story=2013, subscribe=15, topic=537
- Story routes: 2013 for 671 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7c464772d8d10ca8bdfcf90638223ccfd4c680b1c2ff440433471311ad027653`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `533a22fc9c4f163812a84b790d4c2f8bdbc821a799422c07487d22368c3fe3c0`
- Candidate tree: 19247 files, including 2025 local story-media files; SHA-256 `3ce325327fcca49e3d0d3981461a53c23a761e605add8d35d64a2fb028432284`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
