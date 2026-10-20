# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-62e7468c19065c1dc7f797e9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T12:14:36Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4878 routes; SHA-256 `ee2ff62bf90e7d7375a29d3440149a2b708d9f5b895b43b3efc998abbb68fede`
- Route locales: en=1626, es-419=1626, zh-Hans=1626
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=12, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2313, search=3, status=3, story=1833, subscribe=15, topic=522
- Story routes: 1833 for 611 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3cc365e53fab6e565ceb8ff2aa6711277a5eb688211ce1b7bf36c2c7b8157428`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7b74a5156568c1da01a59e76174b1b2f8b1996969190e7d1c8af5cb38be60b3a`
- Candidate tree: 17588 files, including 1845 local story-media files; SHA-256 `0c42bd55de75b85e63ac01830f734550bdc95e0904279197bd520ae3b1e16fe4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
