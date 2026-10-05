# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a8ab11584169f896e64e2c0c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-05T01:39:17Z`
- Edition: `2026-10-04` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 510 routes; SHA-256 `79392d15dcf222111efcae4f90e125a0c3b492ba81a79a90c3c523b05fe9bd27`
- Route locales: en=170, es-419=170, zh-Hans=170
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=69, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=204, search=3, status=3, story=123, subscribe=3, topic=36
- Story routes: 123 for 41 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a8a5ecb07e396e075d725c2b71d80f6aa19751bc5a00fe405032cc799a9939d3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `122fcaad8a39b1704c330d93eaccbd5478abc577085e3292af9ed82c840b7408`
- Candidate tree: 1904 files, including 132 local story-media files; SHA-256 `58caba864b49764d7e67f8754b9c4f2ad6f4c2bafc3afc5601772898e1fb0f72`

## Verification boundary

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
