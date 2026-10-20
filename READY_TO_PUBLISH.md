# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fb3a2166fc299afbe26fbdac**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T05:11:44Z`
- Edition: `2026-10-19` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4833 routes; SHA-256 `9a9131e52d661838dfd442d34400f0a4877b44787fc7c0b1053529d52d5bc6ba`
- Route locales: en=1611, es-419=1611, zh-Hans=1611
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=114, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2304, search=3, status=3, story=1809, subscribe=15, topic=516
- Story routes: 1809 for 603 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `485b9a83096d35c1002f806ec16e4fbfb4d471473c3842f0eaf765e3626ae160`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ae663ec5f9b6dfae30599a59b4cca32d5803ed5d13746f2936f7eedcc7e3b5f1`
- Candidate tree: 17390 files, including 1818 local story-media files; SHA-256 `60a62540404563465ebf84bd4d2f4d98bee771cee1fe985abad65da814297ee8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
