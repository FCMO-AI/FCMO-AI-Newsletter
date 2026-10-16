# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6149b3dce6fe85fee8652c51**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T05:06:18Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4266 routes; SHA-256 `e00b4ad8ee20ac1b3e64cbdf67a0a72f6330ba659cfacd757ff4489415cb10ea`
- Route locales: en=1422, es-419=1422, zh-Hans=1422
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2055, search=3, status=3, story=1578, subscribe=15, topic=441
- Story routes: 1578 for 526 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d1769890b3eac40fe1a0e71e121276b8107f4a1cc4a1531a29ea6124ad8ab375`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c1a90d0298029656d3a376c57659d09afdf2eb2247b570347eb663d0cf06cc12`
- Candidate tree: 15331 files, including 1587 local story-media files; SHA-256 `75e58c33718eb84f991808089d9e003a5ea5a56156abbe81e1485f84f9b93d88`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
