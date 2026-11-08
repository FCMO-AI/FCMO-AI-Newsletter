# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-248ef6cb1b01063a69465ed7**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T16:05:37Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7125 routes; SHA-256 `1abaf4bcd7cce923fb5a09805fe9bad80cecc97b030655f04b68f4f2cac161e6`
- Route locales: en=2375, es-419=2375, zh-Hans=2375
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2775, subscribe=12, topic=753, topics=3
- Story routes: 2775 for 925 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `6e3325b10c49aaea2151d27593f9b3015304065258758cc56d48d50b781fc7ff`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d58824dc0aba2fb82a7dd0ce0109277660b287322c46f0a2272b4b7a43a95569`
- Candidate tree: 26104 files, including 2790 local story-media files; SHA-256 `bca409c9b2553e038ff57c079b7ac0ab7a503b3abbc745072c47d74c1dde55de`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
