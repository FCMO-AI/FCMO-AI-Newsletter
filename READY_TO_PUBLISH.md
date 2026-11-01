# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-daa2ae5cfa172561e67e0449**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-01T23:28:06Z`
- Edition: `2026-11-01` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6483 routes; SHA-256 `12c495b7b0fb954830b0960caf7081a5434522713f7f5539a8d91d9c96b0bb2b`
- Route locales: en=2161, es-419=2161, zh-Hans=2161
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=153, feeds=3, landing=3, legal=9, letters=3, method=3, org=3027, search=3, status=3, story=2499, subscribe=12, topic=678
- Story routes: 2499 for 833 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a51c69b53f7ae47fa0af7d2f26473d4af66b2012ba258756a4fef4f2d5f15143`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4dd4bfbd1b955dc62d91cf07f151ae9ec1f69d38be2d4d2a284d1abe0357478f`
- Candidate tree: 23643 files, including 2514 local story-media files; SHA-256 `347826da0d8b3c3a7151775b147a8634b947739bdeba99404464d093e6ff0ca6`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
