# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-44dc628eb04630ba328ad135**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T11:50:51Z`
- Edition: `2026-10-16` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 4416 routes; SHA-256 `849d9f96eb971a4fe0430d9b20d8b8fe19dbcb1be1685aa361ab08aa2e1c6428`
- Route locales: en=1472, es-419=1472, zh-Hans=1472
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=105, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2100, search=3, status=3, story=1653, subscribe=15, topic=468
- Story routes: 1653 for 551 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8ac709ad489a02c2db53c8a6761c5aa987706c72d9b934dc5d7eab66837f1026`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4f2ea4c4e5f0a6160706bd6170f0d9a5a4a9e8d549d22aeaf5af834975a15522`
- Candidate tree: 15949 files, including 1662 local story-media files; SHA-256 `f6eeec4d9b97521e62c6e8cdb05e2dc3578d1d6a1521014d7e20cbc91fa73c35`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
