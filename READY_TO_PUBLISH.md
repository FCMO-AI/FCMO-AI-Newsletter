# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eba6ef1a8a7dc12a58f623ff**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T10:14:28Z`
- Edition: `2026-10-16` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4404 routes; SHA-256 `ed25d625e910dac1cb25d5b67709a5214b4ae3c31e8e961711f9dbb1d5394d13`
- Route locales: en=1468, es-419=1468, zh-Hans=1468
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=105, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2100, search=3, status=3, story=1641, subscribe=15, topic=468
- Story routes: 1641 for 547 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `039398a63f7d97cbd0100ab0eff1eda6f6ce7483bd2c9af7d7cba673f44e6ef6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e51d576197b716d4b9061ba46c8c59e695381a5b62eeda68bd3b05aa14dd7a6d`
- Candidate tree: 15864 files, including 1650 local story-media files; SHA-256 `f9e0b0abc6a968376fdb32eb3c06ae2188f1c08074a9013de498eca43584fd2a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
