# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-9c7b5bd304a5f6ee822d9497**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T04:32:27Z`
- Edition: `2026-10-22` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5289 routes; SHA-256 `1257a1bd6c70364918fd15cb588f5025c14005736735aa026cca22b4e264de36`
- Route locales: en=1763, es-419=1763, zh-Hans=1763
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2517, search=3, status=3, story=1992, subscribe=15, topic=534
- Story routes: 1992 for 664 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `36d4022a815f5534df609e8d1f39db82542b5db0a05f895d57b14a0edd7e261b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `a2fd9d42a74992d69e4698ca41205f83ab1f033e3285db96f3e430a4aeffeec7`
- Candidate tree: 19042 files, including 2004 local story-media files; SHA-256 `cace14b7bd05805e0cc649d6396c5442520efe45acafc528f4a05844c0f0294d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
