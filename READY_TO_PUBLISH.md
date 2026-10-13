# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fe08b092d85e5fe022624d0f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T09:01:07Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2946 routes; SHA-256 `08ce68bb44c036ade47c69cd3458ba3edb959f0038244f94a0cc2cf55681161c`
- Route locales: en=982, es-419=982, zh-Hans=982
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1449, search=3, status=3, story=1014, subscribe=15, topic=297
- Story routes: 1014 for 338 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a402a7e740d68095aad991907d475123693ac8584133a45972e7a78108a3a587`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `52319b4cc3d902a269d0f311e1ad39f3b77773ae9d96e9d1ca09b2f2da5a9535`
- Candidate tree: 10412 files, including 1023 local story-media files; SHA-256 `9670d52a75bc5606548ee8c1934e58edec186574c0458d1bb68b48300cf6d2ac`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
