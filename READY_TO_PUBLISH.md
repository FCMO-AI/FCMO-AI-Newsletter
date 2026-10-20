# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b5754939c6e6c153ae4015f3**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T08:13:20Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4851 routes; SHA-256 `02d1547c9d692e732723b9cc3d62714dfe8f5880586dff98a5810e6585cc6345`
- Route locales: en=1617, es-419=1617, zh-Hans=1617
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2307, search=3, status=3, story=1821, subscribe=15, topic=516
- Story routes: 1821 for 607 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d4591399da856a92430534515b890b71402e23eb9bffb0acb663c76f2aa52a95`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `63e7664b6b65596e3729808bdf41c726d5e704bfbf12f9e2ab1f8ab7c666c5e9`
- Candidate tree: 17479 files, including 1830 local story-media files; SHA-256 `34443424f48ec96867e943ede5b54fd0260ab359190f2b9169706ed70245c16c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
