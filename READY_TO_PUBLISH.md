# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-91622cb6932149237baa9919**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T06:02:24Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3792 routes; SHA-256 `0fe51c14ab44507200a7ed6ef04c5d3adf8c03692a5b2f08c25b3a37d5393462`
- Route locales: en=1264, es-419=1264, zh-Hans=1264
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1836, search=3, status=3, story=1380, subscribe=15, topic=384
- Story routes: 1380 for 460 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `acb1b4421b79d96f1a055fd7c2bee780b68f85d8d801a3eca265742313474194`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `59757ae5f21e41aa7299bc3c81eeaf03ab9b7afba6cc730040fbdaf931f80a9e`
- Candidate tree: 13594 files, including 1389 local story-media files; SHA-256 `259577e9763b474787cc81b61dd3584f55f6a33272688a934c23c9c8dee2ac3a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
