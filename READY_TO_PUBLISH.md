# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-20c466f170839ac07e07bb80**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-09-27T00:54:13Z`
- Edition: `2026-09-26` (`TRANSPORT_DOWN`)

## Final route/data manifest

- `data/routes.json`: 468 routes; SHA-256 `d5900dd1ef6f8d6dcc35b39e3dfc4bc3127638930ca13d394c97e487d05d8e85`
- Route locales: en=156, es-419=156, zh-Hans=156
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=27, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=204, search=3, status=3, story=123, subscribe=3, topic=36
- Story routes: 123 for 41 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `653f98d732de40038b5269be1c3d6e23a7542a63e09375f6081ec578c97ad8fb`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f012ab01560193eced0cea47af0dabdd75c1e3914513482001e0810984cdce87`
- Candidate tree: 1705 files, including 132 local story-media files; SHA-256 `273f7199d9042ab38b0e696d71f96fae77025b8440233288ea11e0ad7f3be85e`

## Verification boundary

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
