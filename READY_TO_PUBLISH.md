# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7598cbc0bdc64b6908ed5abf**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T00:49:54Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1419 routes; SHA-256 `901eaa105f63f813c367085eb70caf03ee7a92c7a33da35334ce20d470c58881`
- Route locales: en=473, es-419=473, zh-Hans=473
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=672, search=3, status=3, story=438, subscribe=3, topic=150
- Story routes: 438 for 146 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `812a20955147a1eac119c52bad049e1016498298ca7c915f3968351f1e8735f5`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d07e459348d3250772a27ac6f94e281b4f9205df43feac27f8d9caa526074468`
- Candidate tree: 5042 files, including 447 local story-media files; SHA-256 `7d8e08f1ab4dcc9b3d3d2d55e83fca2a3c3b4cb302fea8640e08cf4864888e45`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
