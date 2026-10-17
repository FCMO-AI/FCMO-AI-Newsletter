# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-04928b1be6b5bb08c0572fa1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-17T12:15:48Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4518 routes; SHA-256 `9aa84f3f88aa67d681bebff90b780abdc141ade08cb57920c9b3c7dcbd1908ac`
- Route locales: en=1506, es-419=1506, zh-Hans=1506
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=108, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2160, search=3, status=3, story=1680, subscribe=15, topic=480
- Story routes: 1680 for 560 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b534b39e021ad386681539c8f664c6df3a1d6f04c971fb77450e38388bdaa996`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e27a5654f5f2874629b91f8f397273e332b3acc1f37b3de7b4fb5c637ebcb936`
- Candidate tree: 16244 files, including 1689 local story-media files; SHA-256 `a5bca1ccc19e478a182e0896943d624e4f57e7f2fecc67117a01603d9335eb49`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
