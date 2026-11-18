# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4d805b9883cc6d69fc34f987**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-18T18:44:11Z`
- Edition: `2026-11-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7545 routes; SHA-256 `d756718e3219fa851fc6a7a37c03312b11aa03fc0cecb8c82294426743c8ca95`
- Route locales: en=2515, es-419=2515, zh-Hans=2515
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=195, feeds=3, landing=3, legal=9, letters=3, method=3, org=3447, search=3, status=3, story=2967, subscribe=12, topic=798, topics=3
- Story routes: 2967 for 989 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d71b1b146f9ccf12561ed33137e21c2a84d8f6a442e0af693c860629279c2dbb`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cb76889ff271276b084a3f3ab7991341396a373e554491d3321f1a611e12af8b`
- Candidate tree: 27810 files, including 2982 local story-media files; SHA-256 `da1203c54e9518a5033a273d618f866fac256b0c26a9a33510a2e61b12c7b48c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
