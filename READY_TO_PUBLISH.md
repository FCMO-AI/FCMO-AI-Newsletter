# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2194e08eb4e4bab0c0ad32d1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-17T05:09:06Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4473 routes; SHA-256 `23990cc98b9ed4e1a94168edb139d0cc979c428e5dda3090cb10cec2d29a23bf`
- Route locales: en=1491, es-419=1491, zh-Hans=1491
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=105, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2145, search=3, status=3, story=1665, subscribe=15, topic=468
- Story routes: 1665 for 555 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `70f2d3f49212d3fa7cd3e4b1ad2f6b1817f69c233696ee2303105c4b54d427aa`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `23aa507de9465b549b7fc4d8a60bb1c3a160761b1d2147778508452be8f8fa20`
- Candidate tree: 16096 files, including 1674 local story-media files; SHA-256 `eb39700d0d0e91e28ca858b66cf7dbe3e750387f3220598023befc1fd88cf342`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
