# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-078cd08ec0d14244472229de**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T11:18:16Z`
- Edition: `2026-10-24` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5463 routes; SHA-256 `8719501ac229764111b59e5a0f553f04eeaa2b740e0663f36fe5fed0546794d3`
- Route locales: en=1821, es-419=1821, zh-Hans=1821
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=129, feeds=3, landing=3, legal=9, method=3, org=2610, search=3, status=3, story=2061, subscribe=12, topic=555
- Story routes: 2061 for 687 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `59482d7021cc67955b450bb20a5819d2c4a1cae4540dc54ed0be4f57beca052c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4ee530f6e1f84cd26813f82c987d1bdd5faeab20e55898da7e4b2fb0bc932b54`
- Candidate tree: 19711 files, including 2073 local story-media files; SHA-256 `c2452bc6b192b6465989ed176102b0d057aa87051ad1394fc6d7fb27db710db0`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
