# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6b08b5c7f58a48b86415a98d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-04T06:35:11Z`
- Edition: `2026-11-04` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6798 routes; SHA-256 `ac668fa563f007ab38db5a03fb064bc7007c1553b1ceacf33fadc34152792934`
- Route locales: en=2266, es-419=2266, zh-Hans=2266
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=159, feeds=3, landing=3, legal=9, letters=3, method=3, org=3177, search=3, status=3, story=2628, subscribe=12, topic=705
- Story routes: 2628 for 876 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `171e7fb07b1b39e171208e915c136a9fc02ccb762c2ec95b8f314d52fb48d9c6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cf4e727b17052f3a94add069d9c95ed57de97eb62722166cb8d46f81867d6b36`
- Candidate tree: 24806 files, including 2643 local story-media files; SHA-256 `3ce321a2a68716253ca59c697afa58e1c0a59c2ef07617fe6e5cc8b29b90c95e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
