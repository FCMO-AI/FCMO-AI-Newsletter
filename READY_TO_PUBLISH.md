# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-677c10ab70899c7f77f287a6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-16T04:46:02Z`
- Edition: `2026-11-17` (`QUIET`)

## Final route/data manifest

- `data/routes.json`: 7479 routes; SHA-256 `15ca3aee39313b8b8462c5c0445512b79d083f7c719d7b5e167111db9579befc`
- Route locales: en=2493, es-419=2493, zh-Hans=2493
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=192, feeds=3, landing=3, legal=9, letters=3, method=3, org=3420, search=3, status=3, story=2940, subscribe=12, topic=789, topics=3
- Story routes: 2940 for 980 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `899160b2b9680d0e2c211eab040770cd46cdbc3b42ce211b2bd5d2d39181fa75`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b9f7cc399dbd5915e016db22eff87e8463f8be1532b60a7280d9f757bb142462`
- Candidate tree: 27564 files, including 2955 local story-media files; SHA-256 `a564472d2bf0a30da3bd735c373f565b3617fa629ad3146044dfa49969cc1ffe`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
