# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2295e1c92a912a2a6abf2cb9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-17T18:09:07Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4548 routes; SHA-256 `1881cdab81742eed1897c0eb0c2ba3029ad07183cbe8f9de1e8d026536981f84`
- Route locales: en=1516, es-419=1516, zh-Hans=1516
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=108, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2175, search=3, status=3, story=1689, subscribe=15, topic=486
- Story routes: 1689 for 563 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `95a90f64f11e567d1166e746d6e3988e1bf39c7e35a99fff305128d0b5894452`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `48a1e23f05cda7318dabd25d1526c63fd4be4a7efcc24516addb2f520347af46`
- Candidate tree: 16340 files, including 1698 local story-media files; SHA-256 `bdd45efb50f530e7c3b425396f5fd07671dcb566208ab2df2c2019339cbead6e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
