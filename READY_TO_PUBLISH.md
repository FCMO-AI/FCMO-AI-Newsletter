# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c0731daa041eb9680c47b95f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T12:18:30Z`
- Edition: `2026-10-25` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 5463 routes; SHA-256 `2c8547c802d01e349203d7b484d68a47ca1c5a788f01b5a5eb2679c9c9dd46e4`
- Route locales: en=1821, es-419=1821, zh-Hans=1821
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=129, feeds=3, landing=3, legal=9, method=3, org=2610, search=3, status=3, story=2061, subscribe=12, topic=555
- Story routes: 2061 for 687 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7b12e06feaa5a31068298984166de220045eb46a6a4318447811dbab638f5e14`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `dcc044d5c4576610139de98a31284aa88f5c089dd3056e650db259d8be69765a`
- Candidate tree: 19711 files, including 2073 local story-media files; SHA-256 `444f2b89c35f83712ae11e9892f13ae45ad27e23c2bf0414e7efe6614a4c861a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
