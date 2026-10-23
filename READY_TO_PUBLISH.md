# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-82475fe75b9ba267876acba7**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T06:16:34Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5298 routes; SHA-256 `3dc641b19676f56513230417a0482d2138ebc853a94347ab163e449b3780e348`
- Route locales: en=1766, es-419=1766, zh-Hans=1766
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2520, search=3, status=3, story=1995, subscribe=15, topic=534
- Story routes: 1995 for 665 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ca05d9eb4c60af78b6cfb7100fb10f3d4024cdc959e46112da9e57270b676aa8`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b43ff9a326bfa192424911aa1ae4c9a90a372a98f4d5b801f81a8400835cb3d4`
- Candidate tree: 19074 files, including 2007 local story-media files; SHA-256 `45c72c6949f91e96c862bd3fa7b7dcb969c09d8f3aeb6e087b89196d70516b17`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
