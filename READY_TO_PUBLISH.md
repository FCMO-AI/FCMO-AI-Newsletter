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

- `data/routes.json`: 459 routes; SHA-256 `297ef9e705030e9ca2b1772554797e637e8f9678b89562543c0e525496f8d9ce`
- Route locales: en=153, es-419=153, zh-Hans=153
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, corrections=3, edition=27, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=204, search=3, status=3, story=123, subscribe=3, topic=36
- Story routes: 123 for 41 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `653f98d732de40038b5269be1c3d6e23a7542a63e09375f6081ec578c97ad8fb`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f012ab01560193eced0cea47af0dabdd75c1e3914513482001e0810984cdce87`
- Candidate tree: 1696 files, including 132 local story-media files; SHA-256 `683cc9c5465261af3ff9b139cdb370e7cb23caae480708a2a9adde047c1e6610`

## Verification boundary

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
