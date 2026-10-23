# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e51c128e8a36c929739275a4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T19:47:38Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5379 routes; SHA-256 `9f07252c2908ec4db719ec7e018ff052daba27c10ff0e030482849a8e8027bec`
- Route locales: en=1793, es-419=1793, zh-Hans=1793
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2562, search=3, status=3, story=2022, subscribe=15, topic=546
- Story routes: 2022 for 674 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7da949adde8ce16b8467581aa82ad507e17d9571e9af426a8c99d5995bbad857`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2f4dd848b88c613abe83f70f81fa1bbe0c42bd9d8daae1fe8eb3a6d09d7eb56b`
- Candidate tree: 19342 files, including 2034 local story-media files; SHA-256 `520fab2e255e1b1ae81e79c846b4d129efdb83896da195b5f8944a09590b7507`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
