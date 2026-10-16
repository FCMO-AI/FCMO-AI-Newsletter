# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-367ecead23d5377df5a7facd**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T09:09:51Z`
- Edition: `2026-10-16` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4371 routes; SHA-256 `16296562111028cc4506a2f1729f24abe87c53d4823834c75a6bcd6242cf8670`
- Route locales: en=1457, es-419=1457, zh-Hans=1457
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=105, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2088, search=3, status=3, story=1626, subscribe=15, topic=462
- Story routes: 1626 for 542 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0a3f0171fd961cfc768c9d2253bf2dcf02c9ba8257d4d180e7454f3aa31e35cd`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6baaa2da24bff2710f9ebc9e654bf1a9ce92b768b05d790906c7c6b174bc6a66`
- Candidate tree: 15742 files, including 1635 local story-media files; SHA-256 `442200267871495569a1b291a4a4d2845ea34fd3ef98023f5b176dbad1e80790`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
