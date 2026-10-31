# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c55f27f09e9bf8e1da96c396**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-31T00:32:28Z`
- Edition: `2026-10-30` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6279 routes; SHA-256 `ead4e05d14dbcd4a07f781ee03f60521221e06b4dfd6b1876e6237b27aed4a7c`
- Route locales: en=2093, es-419=2093, zh-Hans=2093
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=147, feeds=3, landing=3, legal=9, method=3, org=2919, search=3, status=3, story=2424, subscribe=12, topic=666
- Story routes: 2424 for 808 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c6da3911107705f3463d007ade49a4e61edcb663574f940eef04d79ce09153d8`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3f42236b545cc2187142b511d2cbe13f2f6005e89caef233b44ef79aa78908d7`
- Candidate tree: 22891 files, including 2439 local story-media files; SHA-256 `a24b97dae733a54358080aedd6bf70eec2998d0d569c0fd065eec17e66b9de2b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
