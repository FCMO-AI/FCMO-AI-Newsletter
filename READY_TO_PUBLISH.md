# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c9419985f3bac6b133ce5708**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T09:13:09Z`
- Edition: `2026-10-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1614 routes; SHA-256 `61a419096d60c9f43794ed64dbea9a529310db2be732c3559b47a8d3f3d64742`
- Route locales: en=538, es-419=538, zh-Hans=538
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=84, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=780, search=3, status=3, story=498, subscribe=3, topic=174
- Story routes: 498 for 166 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b9a00d914523956093b7c0ba9e5f8f0e4c7cc9552404eceabe300b27bee90ca0`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cc2474b3e1256ad477bb91c265c4e69d0e9eba416e53de8bfce0afd39cde3a75`
- Candidate tree: 5658 files, including 507 local story-media files; SHA-256 `835539ef26546f1755066f6ad0a6574f5acdf57843eeae782a3508f3c0bc56a8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
