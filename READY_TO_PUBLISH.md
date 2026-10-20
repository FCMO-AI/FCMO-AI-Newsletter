# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-67e7293bac394ac05ed47f40**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T03:10:15Z`
- Edition: `2026-10-19` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4833 routes; SHA-256 `48510b0516d802b2edf2140a5569f6f7b8ff0c31e8f93ab4b1175f8e63ff2543`
- Route locales: en=1611, es-419=1611, zh-Hans=1611
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=114, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2304, search=3, status=3, story=1809, subscribe=15, topic=516
- Story routes: 1809 for 603 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `f73c6e02ab65037a29837d782c43a445170b6e334cc0883898b179f0f9778e95`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3ca12c556a694f5bd1f9808d99b611fc431a4b691c76d9afa2e2522ee2ffcce5`
- Candidate tree: 17389 files, including 1818 local story-media files; SHA-256 `8873b9ea5a8043c7126a109fa695916c49195d2d7ceff7bf5426151b4ccbe6c8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
