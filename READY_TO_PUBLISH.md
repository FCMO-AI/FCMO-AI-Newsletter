# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-df405a5f53f391e8d3774a38**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T11:36:34Z`
- Edition: `2026-11-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7134 routes; SHA-256 `503f610f83dca3e7fef10f121f2a4f0cff97c36de097629793a5da9d11537064`
- Route locales: en=2378, es-419=2378, zh-Hans=2378
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3294, search=3, status=3, story=2778, subscribe=12, topic=753, topics=3
- Story routes: 2778 for 926 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `e187d983967f48083f73bba4ba5ab890d863b3724461782813539e83e98ff98b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `66f9fc40aebcf7630ecb5b57a877e29b6dcb020883646a39a7e23e988d551ced`
- Candidate tree: 26137 files, including 2793 local story-media files; SHA-256 `d1da0ff57781d709fb7b86e138e7df15e727e296f52e05c8fb7292bb8fcf3bb9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
