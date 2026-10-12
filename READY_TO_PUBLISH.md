# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4f6814e2061aa9acf11abedb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T12:57:13Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2724 routes; SHA-256 `7edb27603bc473ac861039dfc3d2f15b122067428edbaded7a5500831c530e48`
- Route locales: en=908, es-419=908, zh-Hans=908
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1350, search=3, status=3, story=921, subscribe=15, topic=270
- Story routes: 921 for 307 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b57af8c62a21daaa1cd941f4b8660ab93e6719351e9c32a663575b2bc96cdc6d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4368a04b173ad9c3aaa1f2b04f98b3401124389782786d9f2490d0a48913ed53`
- Candidate tree: 9576 files, including 930 local story-media files; SHA-256 `5fd8e394efa0950977cea5828f0b4fccae714cd382bd58a85c2f0d0f186cb24d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
