# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-9cd56eab52311e359b2995e6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T17:15:10Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5940 routes; SHA-256 `0fadf3ac558277a28c1db4603a49d8f05837e3f54cbf5cf9f3e7a223e1daaf82`
- Route locales: en=1980, es-419=1980, zh-Hans=1980
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2784, search=3, status=3, story=2274, subscribe=12, topic=621
- Story routes: 2274 for 758 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `2701cf261168c99ae18b48259149e87c7a53940232e29a08532cfcee7e99f64d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `97bbd8e20ac6f923ca722645bfa43ee1b7696838ffbca5c6bbd61a8ebb0cb458`
- Candidate tree: 21570 files, including 2289 local story-media files; SHA-256 `96a720897d36deaec3552e3afc518fab2dd90c034c2dec689bc43f6a6417aa3a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
