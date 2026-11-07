# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d7540ada8fd0caf72421c3ff**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-07T01:57:27Z`
- Edition: `2026-11-06` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7062 routes; SHA-256 `ccbdbf465375ee34b2ba9a6a6caffa7153d451cf4efc2e7c58b97890eb395be5`
- Route locales: en=2354, es-419=2354, zh-Hans=2354
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=168, feeds=3, landing=3, legal=9, letters=3, method=3, org=3273, search=3, status=3, story=2739, subscribe=12, topic=747, topics=3
- Story routes: 2739 for 913 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `abd812420943cd8b7cc6ce25c7e64a1c18e0ff8d0028b2b837fdee2efe8c4167`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ae46e6dce932a7535d4adba4b48daaecc89c7b9bee97b02b5e47af782cefb384`
- Candidate tree: 25801 files, including 2754 local story-media files; SHA-256 `3036ffcfde3012940085dee083fcaab964e67cba6d43c605086f46359fc1eccd`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
