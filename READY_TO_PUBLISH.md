# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a2517e87d49d28233208f5bf**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T07:11:42Z`
- Edition: `2026-10-22` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5154 routes; SHA-256 `ff01ab0c4f98e29a3fd6b4a00afd88a5027553cf04eedc60472cf328405a3b60`
- Route locales: en=1718, es-419=1718, zh-Hans=1718
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2442, search=3, status=3, story=1941, subscribe=15, topic=525
- Story routes: 1941 for 647 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `25a0fdc0e124432f07aa705f8e6e601e7e4a105c1bb5a6433de1055edc3e40b1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3ddbf6da6944add6557d9e2d4463f8a9dc93e1c67e88480c76e163b2c21a8f23`
- Candidate tree: 18565 files, including 1953 local story-media files; SHA-256 `3f295eff06e947cb17f5446f2045211d1d0f782850e61e20088b08a917f999ee`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
