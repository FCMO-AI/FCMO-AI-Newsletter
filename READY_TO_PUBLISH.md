# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f407d38f6fe72112bb7953e8**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T14:40:35Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7125 routes; SHA-256 `b0e986bf717770e4f5960d33e29e0f8bd81d588cd20eec41cb1d26f513e7f0ef`
- Route locales: en=2375, es-419=2375, zh-Hans=2375
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2775, subscribe=12, topic=753, topics=3
- Story routes: 2775 for 925 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d43d4890c7e255d47bfb66f700714339f2779bb657bda8129a86ba05e718d344`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `04c0cf6d5b909a4f5ca94eda7ac68b411c53e57178d8a2ad5cef081b717c0905`
- Candidate tree: 26103 files, including 2790 local story-media files; SHA-256 `9a75a0ed40493c57e13e3d7fb1978eae34c8802890cf4cca56cab0ed12c81570`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
