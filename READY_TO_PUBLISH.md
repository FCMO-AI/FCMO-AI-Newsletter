# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-37657899f23134178b1406ee**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T02:21:07Z`
- Edition: `2026-10-22` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5283 routes; SHA-256 `d1a13964c402a4a4a2876bf4df8818e1a0cf98dead056187eb8a93590e34f5ad`
- Route locales: en=1761, es-419=1761, zh-Hans=1761
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2514, search=3, status=3, story=1989, subscribe=15, topic=534
- Story routes: 1989 for 663 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b5087c67c72a2f730877a381f233f3e7b1b2ddcb6edd95f5775c712ca3a16371`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `088ec9d078f26d9c47efc5033574953718ab812c3e948409a0a8e478380bc5b6`
- Candidate tree: 19016 files, including 2001 local story-media files; SHA-256 `24804929b97e7000ff3b2d95e234ea6179d59b05b4d7ad0781a08178c1f44f7b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
