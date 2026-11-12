# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-30328a064861f5b9c3ef475d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-12T17:41:43Z`
- Edition: `2026-11-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7407 routes; SHA-256 `183908506a1857018dab16d9765a444be360f8eee4a2efc1bc6a66b3677f6a3f`
- Route locales: en=2469, es-419=2469, zh-Hans=2469
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=186, feeds=3, landing=3, legal=9, letters=3, method=3, org=3396, search=3, status=3, story=2901, subscribe=12, topic=786, topics=3
- Story routes: 2901 for 967 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `f12f60985f5cb5f0bce897d539e053707200faecedff7a374c77d911c37fca4a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0262060307b7f7ad2236a64b7c934711f29ca819ee5dae02331e58d500d8f06a`
- Candidate tree: 27231 files, including 2916 local story-media files; SHA-256 `2dca8a812425c8280286df61f8c0f4d95c69bc30db71f0fa7c064b5d317d3757`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
