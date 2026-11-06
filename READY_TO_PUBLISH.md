# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3504d6b6252c9a3438c776a4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-06T12:08:54Z`
- Edition: `2026-11-06` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7035 routes; SHA-256 `07df9edf6bc8b5578c744aceee0d69242ddce885bd5eb91e980006995ffd4d17`
- Route locales: en=2345, es-419=2345, zh-Hans=2345
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=168, feeds=3, landing=3, legal=9, letters=3, method=3, org=3267, search=3, status=3, story=2727, subscribe=12, topic=741
- Story routes: 2727 for 909 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a432f3f583acb100ff8da6dd769ed79709046d25315cf18878329e4499591d06`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e32e99e81a4a7984ef74722e747fc9b7539e9a47e3e1ae95dfee390599e6e68a`
- Candidate tree: 25702 files, including 2742 local story-media files; SHA-256 `ce5cccce843139568afc2a391de6f4597ebf02d14acc91a800e53d0a55ac7481`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
