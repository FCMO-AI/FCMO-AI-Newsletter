# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-47e53670d720fba539143819**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-26T18:23:02Z`
- Edition: `2026-10-26` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5610 routes; SHA-256 `809822e792c13f9e0208de967d1a13e30664494957332f4a913a95054e219d6b`
- Route locales: en=1870, es-419=1870, zh-Hans=1870
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=27, correction=15, corrections=3, edition=135, feeds=3, landing=3, legal=9, method=3, org=2673, search=3, status=3, story=2115, subscribe=12, topic=573
- Story routes: 2115 for 705 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d40468ed68a29f7143237fcdba87e99f74de8b2cee1a851ff32c8756f84358d2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `fa8f3f9bc78da3e9867b78fd6b6617bd0bfc020531454034928cc07d8a24865c`
- Candidate tree: 20229 files, including 2130 local story-media files; SHA-256 `0bf5e1314532abc3bdf1e3b75785158387ec1fb75480f0ff79389ea15bc0ed87`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
