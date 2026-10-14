# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a26ba1623d96beac73c7e171**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T07:02:53Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3414 routes; SHA-256 `2761b3bea02b96ef420e0d6a0ea7f49d0f741228416480cfb21792025b06aee8`
- Route locales: en=1138, es-419=1138, zh-Hans=1138
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1659, search=3, status=3, story=1212, subscribe=15, topic=354
- Story routes: 1212 for 404 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `56e07b7e76bcb3e23084750b9d3af4185d6debe24c35805104654c0aa38725a5`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0ad26e90c91ba56e752c057ea56eb0366cf244666c921ba1c711fd8a23c7714d`
- Candidate tree: 12141 files, including 1221 local story-media files; SHA-256 `7c85a9d69241bfe753c60c052d2c84822d3eb3d97052cc523bbb716d53144d85`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
