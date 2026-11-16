# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eb6702703314ffa0904c5f27**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-16T01:41:52Z`
- Edition: `2026-11-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7467 routes; SHA-256 `f601ae40b638aceb32aa06f299dfee8451c5c5317584692203bf0a841de712ef`
- Route locales: en=2489, es-419=2489, zh-Hans=2489
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=192, feeds=3, landing=3, legal=9, letters=3, method=3, org=3414, search=3, status=3, story=2937, subscribe=12, topic=786, topics=3
- Story routes: 2937 for 979 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `050b77d9ef3b5dfc6e35b836256c2b9001af95ee7b561b4696f27b2d7ecb516c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `728d5c1efe5d0983eed637f8d28e507f23c6155a357fece21f35479d89965f08`
- Candidate tree: 27530 files, including 2952 local story-media files; SHA-256 `37cc24e471b3956a656160a9bd3daece1ea9d93325aaa73e1286991f6e0f42e7`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
