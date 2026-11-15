# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5cd8ed92343c20cc6c91e641**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-15T16:32:52Z`
- Edition: `2026-11-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7440 routes; SHA-256 `7bde6f88b8893344f51b6568c2d4c36c723cc142cab41a518872244749df9184`
- Route locales: en=2480, es-419=2480, zh-Hans=2480
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=192, feeds=3, landing=3, legal=9, letters=3, method=3, org=3399, search=3, status=3, story=2925, subscribe=12, topic=786, topics=3
- Story routes: 2925 for 975 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `bfb06d4ee1486e7ee187daf5096d3e515239ff0c093c607baafe7bc881bb4e02`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cddb0fab4aa374a77871f225549f3cadad7f47910e2e849684d6843a00ed9dec`
- Candidate tree: 27422 files, including 2940 local story-media files; SHA-256 `f14b806c0b9a90a7a3ab70340221356fdcf6faccfa3a8b16a6384c31abb613db`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
