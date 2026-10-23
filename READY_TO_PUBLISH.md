# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c1c6d788b18733853a9260f9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T21:09:17Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5385 routes; SHA-256 `1db57bf234884b315692c748e7dcae6840589ee5f89f0042791748933189fc88`
- Route locales: en=1795, es-419=1795, zh-Hans=1795
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2565, search=3, status=3, story=2025, subscribe=15, topic=546
- Story routes: 2025 for 675 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `def1e26bea4a89e3ff6c047e1f059a826a6e0478b717775bd3934260f983f017`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `71215b51d82fb21a6b18c2defdc6dfe74825ee6efd008ed2619d18757d03532f`
- Candidate tree: 19371 files, including 2037 local story-media files; SHA-256 `4934aa72957014af915d2bcf0bb40fa89abea61caa9ee1f8ddb85cc4467163df`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
