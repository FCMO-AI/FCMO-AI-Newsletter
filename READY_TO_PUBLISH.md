# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c8cb87df4bad6ed67b6f5568**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T03:03:21Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3744 routes; SHA-256 `d9c5201be30499af0442ea65cbc90ce0c6f6f97e56cfbe0ba9f236a2ffea9a90`
- Route locales: en=1248, es-419=1248, zh-Hans=1248
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1812, search=3, status=3, story=1365, subscribe=15, topic=378
- Story routes: 1365 for 455 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d0febcd80dd98235a2da0cbcd0a06b01653bbde2a3cafdf9226014b08dec907c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3a8ce785687a86481f2f99da97c929e64dc2fe6e6aae7050b0963df5bcfd39e7`
- Candidate tree: 13440 files, including 1374 local story-media files; SHA-256 `ed7e59828b81353304f0d7ab7c7ac6b3c5ff9ded60cbd71671c56fb652888e52`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
