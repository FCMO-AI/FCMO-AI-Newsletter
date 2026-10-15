# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-77d09f25836ff0b28c2488d7**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T09:02:41Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3840 routes; SHA-256 `732b78b44ba52e2b9e7603fc91964078e7eb9248d03b7ebe53e803142abc89e8`
- Route locales: en=1280, es-419=1280, zh-Hans=1280
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1869, search=3, status=3, story=1395, subscribe=15, topic=384
- Story routes: 1395 for 465 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `65cfb15d834f1113a0252fdcc586fbe005629c4dd139356cf84914fbde3f15a3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2bce1004051623873d9f05071b2e4a9562111b6b2b35727221cb24d817a70a32`
- Candidate tree: 13748 files, including 1404 local story-media files; SHA-256 `ce1cf849fcbd1c3a171d89fccb8fcc997c01855b067a48fb364cca5023f24e6a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
