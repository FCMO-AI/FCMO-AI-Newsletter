# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-27cc0432669b05b7bc6e3208**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-27T21:58:13Z`
- Edition: `2026-10-27` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5841 routes; SHA-256 `7474248b8f09b2eee2b721c7ff530893d5554218aa4ec9881d04ac280e69bf79`
- Route locales: en=1947, es-419=1947, zh-Hans=1947
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=30, correction=15, corrections=3, edition=138, feeds=3, landing=3, legal=9, method=3, org=2757, search=3, status=3, story=2217, subscribe=12, topic=612
- Story routes: 2217 for 739 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `67449d7e7c8dd4374163de05d4db6b3ec8ea6704047291e1dbe710a67b835c3b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0f7d2f003397e9f0db77185e287c5abc9a93e7828d9d3b211683e8866c742b15`
- Candidate tree: 21102 files, including 2232 local story-media files; SHA-256 `9e3fb1e0980af736d7fe26e3405969d3df598f5ffef850ac3b1ca5de39203856`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
