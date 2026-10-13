# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2ebba61a4fdc3a25c7fcc0bc**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T07:00:29Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2895 routes; SHA-256 `decac4ec0c939d266c1aa2c197af548be3e3a283d18ade752828c105b830f8ae`
- Route locales: en=965, es-419=965, zh-Hans=965
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1422, search=3, status=3, story=993, subscribe=15, topic=294
- Story routes: 993 for 331 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c1e4e06f6c13e885f16906f73d4fe064995b2f307a0c439c54aa7b03435b2580`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3456d311eec3c003fff60c443e38cb885b62b7d38377cf6df6954f444bb56ff6`
- Candidate tree: 10221 files, including 1002 local story-media files; SHA-256 `173d3a78c3270767a1d96b0713cd83ac8d7b91ea4edc1f8016f6f222f7ff2480`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
