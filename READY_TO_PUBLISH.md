# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-44dc628eb04630ba328ad135**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T11:50:51Z`
- Edition: `2026-10-16` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4416 routes; SHA-256 `590ecf0fd8e60fa45cd2c9df47d268fdabe93bccb4011f9214b8a97664b33eaa`
- Route locales: en=1472, es-419=1472, zh-Hans=1472
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=105, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2100, search=3, status=3, story=1653, subscribe=15, topic=468
- Story routes: 1653 for 551 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8ac709ad489a02c2db53c8a6761c5aa987706c72d9b934dc5d7eab66837f1026`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7be1e1e3f29c3b562a411b8582f093fad5e0c5d1b0e1d0f84ecdd5e3ac94af45`
- Candidate tree: 15949 files, including 1662 local story-media files; SHA-256 `61593ba076cfa189e36c403265fb03fe9d259e7995af3e03f7daa65a7959f78d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
