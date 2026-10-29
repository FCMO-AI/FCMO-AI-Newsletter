# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2cb342d3f4253eaeea9127d0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T08:04:57Z`
- Edition: `2026-10-29` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6042 routes; SHA-256 `52d286ba87c23aa7bd6dab118d7fb0695691eedf33147e5204d4d8b33c81e8de`
- Route locales: en=2014, es-419=2014, zh-Hans=2014
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=144, feeds=3, landing=3, legal=9, method=3, org=2823, search=3, status=3, story=2319, subscribe=12, topic=636
- Story routes: 2319 for 773 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0ab3e053d36652ee9e1736373b8d258789dbb3e570eeb19e7c6a114a7a58d9a1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0d9886d6c2b94bc3a3e3893a82b7482d78822657b5c4ac6dd2e294d16a4817c5`
- Candidate tree: 21967 files, including 2334 local story-media files; SHA-256 `917570c9f688fe6b7d9b849acfcb773057401a3bb1f655133b5a95462376b145`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
