# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-28ed4633d1324388431d5fba**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T02:06:13Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3732 routes; SHA-256 `a79d13566efabf83d6fc17dd433abbe860dce0ceb1dd0666f391bc2ed2c980f9`
- Route locales: en=1244, es-419=1244, zh-Hans=1244
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1809, search=3, status=3, story=1359, subscribe=15, topic=375
- Story routes: 1359 for 453 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a12e9f987fd059cf8f4fbc00257fd26606508507c466de3995b78800b0559da6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `55c4c24bec6b089cba8ff47fd904d1e8b90ad56adbe1a99c8bb0fcf1374e68d2`
- Candidate tree: 13393 files, including 1368 local story-media files; SHA-256 `f1505af94186c96a456ac3005b9df72a8b3a788217d68ffa9a1ade79b6ebe012`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
