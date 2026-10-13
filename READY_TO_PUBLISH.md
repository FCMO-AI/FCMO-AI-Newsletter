# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5aa12965a348b8e1704a9e64**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T05:55:08Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2862 routes; SHA-256 `23f400d21351086b2c1b25908ebb5cd594f6fa43e2be865fa4af75b4127b7745`
- Route locales: en=954, es-419=954, zh-Hans=954
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1410, search=3, status=3, story=981, subscribe=15, topic=288
- Story routes: 981 for 327 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `cb9986d94a5014eded611049e9f772c747aed75f75310e26a3220b74275364e7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7b7e43a0d0d29a57c93a2f307d0f8f88780d398a19f43b061c745c1ef35f4d48`
- Candidate tree: 10103 files, including 990 local story-media files; SHA-256 `2e0d1f5db85d2064fbced0de627750a4d882f0d38903448adec3cab7d16ae282`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
