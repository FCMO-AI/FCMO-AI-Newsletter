# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a9bf2bf0050a9b5bd85d8d41**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T23:07:26Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4089 routes; SHA-256 `6116d3ec01151c1cddabdd4781b3e3ae195c709f3b813089df4442b6cd6b7e39`
- Route locales: en=1363, es-419=1363, zh-Hans=1363
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1974, search=3, status=3, story=1506, subscribe=15, topic=417
- Story routes: 1506 for 502 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c2413399ae59a2d1ce4527dd08e87d1ac27773ebb1b12d49cdcb1f25e0fd89df`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b9d7d5c5f97f4b3be5996a6d1aaf0d6f6225ed5cc71143244bcf8f8c4e5d0dae`
- Candidate tree: 14696 files, including 1515 local story-media files; SHA-256 `351d6aba25edd7603bfacd483324caecb6f95ff9c742cc78985fa78bc3d9aaa9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
