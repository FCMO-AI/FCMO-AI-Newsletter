# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6347ef93d6c0886c0d4d728c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T07:56:25Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2640 routes; SHA-256 `0ac246d9cc55cc8a5845d584a4dae06f52c9b2386b8b39293d674e80d2c86c3b`
- Route locales: en=880, es-419=880, zh-Hans=880
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1323, search=3, status=3, story=879, subscribe=15, topic=255
- Story routes: 879 for 293 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fcfec578baccf6e8410f02a67928971930afda435fdcb57ec330f179539162b9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4072e161bef42cb653d93ff6c8ecf2c3609349534c5bab8e2b8d6766cc7f25ea`
- Candidate tree: 9238 files, including 888 local story-media files; SHA-256 `cee9391025822fdb225e16563201309a490fe0deda10e590ba49a1f335aa4e27`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
