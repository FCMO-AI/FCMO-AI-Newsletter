# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d6c09a2b87cd98edf6119e05**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-13T00:39:17Z`
- Edition: `2026-11-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7416 routes; SHA-256 `867262219be91910e4166531dc901039f350dfc7e770f532fe3947ebe8f9672a`
- Route locales: en=2472, es-419=2472, zh-Hans=2472
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=186, feeds=3, landing=3, legal=9, letters=3, method=3, org=3399, search=3, status=3, story=2907, subscribe=12, topic=786, topics=3
- Story routes: 2907 for 969 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0d3e0a6a83981ed6db5b66405194f97a94365f557ace4364a3d84b9c7d3c94ec`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8c930b1524e40bf5d5d7d3672952cc5a19b667929325a8aa80a421ba9c21dc80`
- Candidate tree: 27276 files, including 2922 local story-media files; SHA-256 `8cf4216ece0e2591c04eee5a0905ee5dadeddf9d350572cf528501c511f2701f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
