# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d01524c6456e8ee1866c4f76**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T15:02:57Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3969 routes; SHA-256 `2df0e3e8de31d87ef2decb09fb9b56fc89b633fcecada29ccde8bf0c5a0753db`
- Route locales: en=1323, es-419=1323, zh-Hans=1323
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1932, search=3, status=3, story=1449, subscribe=15, topic=396
- Story routes: 1449 for 483 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `9358017a07beab66ad8f5cc95b84e45e4c949c0fb63eb2f41f18faa2d17b5617`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `304137181a93ad8b8a9e824ecd925a0a2092d954b17590731ae4fd9d9a81c643`
- Candidate tree: 14226 files, including 1458 local story-media files; SHA-256 `c2b8d92eb25454790432299fced2e6bbec75cfa155fe5853a1afdfd193de20da`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
