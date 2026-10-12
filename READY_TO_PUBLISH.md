# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fccca1bad40643eef3226ec6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T02:54:06Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2481 routes; SHA-256 `d7b088a248dfd06998e633f7a42527e1a6deec8205b16de5d958af31b19918f5`
- Route locales: en=827, es-419=827, zh-Hans=827
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1245, search=3, status=3, story=819, subscribe=15, topic=237
- Story routes: 819 for 273 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8210546f5d9f1d94828574b6ff940191382e68b9858211da778864afd04dfc4b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7bd8af172026b0f000bb968ea006e4eab1db8d42d600ffdab87392167d69d9aa`
- Candidate tree: 8692 files, including 828 local story-media files; SHA-256 `68cbf462830962d3d358d0a356baf17bd3c5d7b1a6963bd4515268f187de24bc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
