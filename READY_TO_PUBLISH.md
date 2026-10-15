# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-53a0d22745c0ac3afd80f893**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T19:07:15Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4017 routes; SHA-256 `2ceb04aa67b98779efbe0592e618dc6078fa5efc2e2673870ec56c03fd3f19be`
- Route locales: en=1339, es-419=1339, zh-Hans=1339
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1947, search=3, status=3, story=1476, subscribe=15, topic=402
- Story routes: 1476 for 492 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8a7f68e60f4a6685fd53c5da3a18876367eeeff1997945caf7a397145eb285c2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `95e6a9273cab612aac93e619608ab030f558e12fb43344e49bb357c111a6a944`
- Candidate tree: 14444 files, including 1485 local story-media files; SHA-256 `f264d9ecb19366df0ae390c85f3174efc7164da14ab324dc5f2c29734ba62410`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
