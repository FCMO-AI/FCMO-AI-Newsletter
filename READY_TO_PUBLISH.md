# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e3946df35ce73fdce15b3a58**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T01:58:23Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3321 routes; SHA-256 `9e73b1f3765a913d85a9127e77cc6e6c1434cf402c5ee213831ee44ea870c64b`
- Route locales: en=1107, es-419=1107, zh-Hans=1107
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1614, search=3, status=3, story=1173, subscribe=15, topic=348
- Story routes: 1173 for 391 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `297f1095fbc05cb92222ccd1f8fd2b9289417947dce0d40ad6a8290889686e2d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `898f1292e44ecf53be335190e6ba8a0bb718c32b7654693923a3f68efa7a5007`
- Candidate tree: 11796 files, including 1182 local story-media files; SHA-256 `41056e14f3ad32f0cc847fe4fc39043590f21c8f266f1bc7f6263cea1776d868`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
