# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4eebaafe75dcafe207547516**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T12:29:49Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 906 routes; SHA-256 `5659aa6b89452d7cc608c1c84a13ef9a8f744df1b7fddc49c85232e646864851`
- Route locales: en=302, es-419=302, zh-Hans=302
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=414, search=3, status=3, story=258, subscribe=3, topic=75
- Story routes: 258 for 86 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `59075ca35276219707f42edb0938a0f182c75661d482f0a3544563185cf12b0a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `dacb1cfd989a5f44efbae0a19dc28e9597cf45096225c07aad49cc84eaa67c2a`
- Candidate tree: 3286 files, including 267 local story-media files; SHA-256 `8660fcb2638c7c50b529c7237de1ec00031e86e852aa662eff94422f3c0c6275`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
