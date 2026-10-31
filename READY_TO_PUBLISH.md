# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c23f3b20b0655341c97e1c73**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-31T16:30:26Z`
- Edition: `2026-10-31` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6372 routes; SHA-256 `028ce45e5bffcb2af53d3c96c6f1d6add7823647baa170c5d1ed1d1d07269435`
- Route locales: en=2124, es-419=2124, zh-Hans=2124
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=150, feeds=3, landing=3, legal=9, method=3, org=2967, search=3, status=3, story=2457, subscribe=12, topic=675
- Story routes: 2457 for 819 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c918549a786f45054a27bebdade19210a2e6a8b85b686f3b73d962b965a299d7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2066f2d3ad47c352bd06a8e249e1de0cfcf002467530b096887bb7f3808b90c2`
- Candidate tree: 23216 files, including 2472 local story-media files; SHA-256 `5b443053c321b230bf067e8c41116891f6121262e489267f7824c8f749afcbdc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
