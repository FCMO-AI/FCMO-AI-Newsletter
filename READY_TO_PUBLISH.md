# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-432655ab1bfd4445a64701c0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-12T15:45:19Z`
- Edition: `2026-11-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7401 routes; SHA-256 `e52de94bb27aff00ca08b145b3cd68783d43c393a26b60a90f9331dedabbbbf7`
- Route locales: en=2467, es-419=2467, zh-Hans=2467
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=186, feeds=3, landing=3, legal=9, letters=3, method=3, org=3393, search=3, status=3, story=2898, subscribe=12, topic=786, topics=3
- Story routes: 2898 for 966 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `47a374070b372544fd3f1357d71f71c58bd223fff884326d9d905e41f0e05cd1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `12e6f92bc54666cca4241db24e83a7e3a87aea45dfa93ca7b9083c88ffdb3cc2`
- Candidate tree: 27205 files, including 2913 local story-media files; SHA-256 `75df15e5ed26566d411f61e1a7f3b962c09714c7b60240fae596c83e9ba0a9cb`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
