# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2a69d0961e9ec602908b76d9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T11:58:17Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7125 routes; SHA-256 `f7c90a8e405bc5b612f6ef67ed178827b2e9304fd5531523afc8b177a9874eea`
- Route locales: en=2375, es-419=2375, zh-Hans=2375
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2775, subscribe=12, topic=753, topics=3
- Story routes: 2775 for 925 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `e459423c6235f39dc2dcf1c3a1859f8cca1761104ec659a289eca7dbdeaf736f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `222421771119212806d3b77fe6c843d23f06d28b2f60c152aa052b5f5c0140e1`
- Candidate tree: 26103 files, including 2790 local story-media files; SHA-256 `39ca075c11b0bcc7aa8dd1da79d3be52a4b99e6709433679615bae1d6642ac88`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
