# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-683343547850f43850428afa**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T12:14:42Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5316 routes; SHA-256 `9badae6a820d0fb8046fdd7eafeb64f952f1602eafb870a7e0badaf08cf9a6e7`
- Route locales: en=1772, es-419=1772, zh-Hans=1772
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2526, search=3, status=3, story=2004, subscribe=15, topic=537
- Story routes: 2004 for 668 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ef18dfb3e07a4f2255055ae78770ec7b971784beaba05bb6c78738de1280ead6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `94c51609640df9ba15e4132a63d4f6c57f5cfb49d1aeb89c8f99b56f4cd8107c`
- Candidate tree: 19154 files, including 2016 local story-media files; SHA-256 `619d0feb41b5210280693a3783e873ab5609c327be52227cbff988348ee02b9f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
