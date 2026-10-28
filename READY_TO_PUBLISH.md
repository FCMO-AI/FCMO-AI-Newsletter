# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-9570e48b55e0c05f31174fc8**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T10:38:09Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5925 routes; SHA-256 `9a57f51130d8fd8e8d659ef01438ad23edb2e23653d0efb72b0337f306018bf2`
- Route locales: en=1975, es-419=1975, zh-Hans=1975
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2781, search=3, status=3, story=2262, subscribe=12, topic=621
- Story routes: 2262 for 754 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `696066fa1e4867f4d618a24881bbd318254355d9f7748d31c20baf0227d09d14`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f881dc99a4dc904d52abee3efd99e0f7eee42ea01cdedc57296c59bf1508984b`
- Candidate tree: 21483 files, including 2277 local story-media files; SHA-256 `e1c09dfebe372b8a6a61e469b5c8daea0cebd76209d562d0d91cc543063111c4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
