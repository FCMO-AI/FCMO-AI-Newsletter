# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2901e846397ba80f571eb9fb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T09:58:10Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2961 routes; SHA-256 `4b5074aca78fbdd5688b1daa4a7310c6e9ff0133dbbe2ec376e364c92bdc4f46`
- Route locales: en=987, es-419=987, zh-Hans=987
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1455, search=3, status=3, story=1020, subscribe=15, topic=300
- Story routes: 1020 for 340 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `be9796b53e7d5c00618c2709df6378076d632b06bf6911004aa2ff9378266315`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e013810794ee6e578aa662c3fe0f6ac3ed69cb8ac9ee23d7559f7e8a9b1f6f3e`
- Candidate tree: 10470 files, including 1029 local story-media files; SHA-256 `621137913215100ff2158e784491429684405cc4cebf339f0f09578cc1d5c7f4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
