# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eb08693f8dd9d1d4672d6b63**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T20:58:53Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3621 routes; SHA-256 `92e851a9e13bbce19708e29d54536cd9e239bc57bede8cc92450c8694a9d2929`
- Route locales: en=1207, es-419=1207, zh-Hans=1207
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1749, search=3, status=3, story=1311, subscribe=15, topic=372
- Story routes: 1311 for 437 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `28dc0b2bcc19a666e733a1e12c88986f07306aea97ed4e41139789a86e2bb451`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `9f220e3c302a56fac92a79898285bdb9f641572fc815cc8fe6838ae250db8277`
- Candidate tree: 12988 files, including 1320 local story-media files; SHA-256 `7891f0d9f33d6b8bf09a4fe4a19a22b5d5221e9d3d6c1096793eda8659fb39b1`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
