# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-456281bba819c092ff2fd0e1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T16:21:25Z`
- Edition: `2026-10-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1758 routes; SHA-256 `3634e707e1b0f3943c0ec148bfe665519a0969560845286198f2ff6025e4d7af`
- Route locales: en=586, es-419=586, zh-Hans=586
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=84, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=873, search=3, status=3, story=543, subscribe=3, topic=180
- Story routes: 543 for 181 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3bcb86ea03793dc6869f3f4aa802c29c8dc51268599fd0d865a58fe2960cd713`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2e02f68f04acd596e1b128779b2aa143d9fc928faabc93695d47d67405910994`
- Candidate tree: 6123 files, including 552 local story-media files; SHA-256 `97d044067e876d6dbb7d9d4d4647974b7d52e9febbe2b15a6d7a84b66c859cd6`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
