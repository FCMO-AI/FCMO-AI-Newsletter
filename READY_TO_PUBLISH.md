# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2d533ea027bca0e60946aa50**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-06T22:33:45Z`
- Edition: `2026-11-06` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7059 routes; SHA-256 `216087528f4c4e49ef19213f49ec6356159af1d155b1208a35a9d23fddf07016`
- Route locales: en=2353, es-419=2353, zh-Hans=2353
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=168, feeds=3, landing=3, legal=9, letters=3, method=3, org=3273, search=3, status=3, story=2739, subscribe=12, topic=747
- Story routes: 2739 for 913 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7d730c863d819581014b3ada955fe90568b2e1d06453ef9fe8e5dd5384cd46db`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `345a511858434ccc635c885c21d06bb8539fbc640b3348e8a5784acc99e91dd8`
- Candidate tree: 25797 files, including 2754 local story-media files; SHA-256 `275c4d80f20903824eb1cfb5a5c358162a1bdc3694dff280a48950cb12eff964`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
