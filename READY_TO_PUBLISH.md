# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ca1e0123f2ad5aded9e9a314**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T18:14:24Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4893 routes; SHA-256 `96520940e49b97af0cb9151c50eada4bae7d2b60e0e9cb940ac7d523383123c9`
- Route locales: en=1631, es-419=1631, zh-Hans=1631
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2316, search=3, status=3, story=1848, subscribe=15, topic=522
- Story routes: 1848 for 616 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `6c0bf55d0208606b9fdde454159435a04eb93a12bf608a580a0903425c9e3951`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8ce07876fd6ae018b8e895095f8897d9e52e496b358dd6238dc4d125d5d0dc5f`
- Candidate tree: 17685 files, including 1857 local story-media files; SHA-256 `b7ff7fa82bd88051334ff9a2f054a1755f67e77c6ed4022aa20f7bd07a7eecbc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
