# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3cb562a74f794a7a4af42368**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-12T01:41:43Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7377 routes; SHA-256 `995078c15e105505a70e35fe8ab11d54686cd6d4f1255ac5f1423cdec33821db`
- Route locales: en=2459, es-419=2459, zh-Hans=2459
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3384, search=3, status=3, story=2889, subscribe=12, topic=783, topics=3
- Story routes: 2889 for 963 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `de702ad6c9db55baa24a61959b820f8c1b7400354b57925a88e7afe1e843a366`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `bcca656b095d58a6562bf3e17e793fdffe057f273ffd2b1dce1e7a4546e8a8a2`
- Candidate tree: 27114 files, including 2904 local story-media files; SHA-256 `b9032acb5ea19cba0bc14287278d2bf326f30040e5caa3793810de6af0c22e79`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
