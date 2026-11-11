# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d83c999791bab3b2111cc114**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T17:44:28Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7347 routes; SHA-256 `0529316be16a556d221bd1b6ee533aa3f1a952a9adbc94704ba4380171b4e91e`
- Route locales: en=2449, es-419=2449, zh-Hans=2449
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3372, search=3, status=3, story=2877, subscribe=12, topic=777, topics=3
- Story routes: 2877 for 959 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c4771015f86418a93669ccaf6738cff5f92c5546634137d53a9006c0990bdeb6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5a4706884c57696b8338cc510fea3c6b7060ebad376e28b6652ea943e666a600`
- Candidate tree: 27005 files, including 2892 local story-media files; SHA-256 `18ab3d8e7200db9cd9568547e1e67150a9cbb279e4ffde7b31b012380a672121`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
