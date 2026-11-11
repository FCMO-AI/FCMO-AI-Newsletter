# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c98b993c94df460343d97c1c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T00:51:37Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7278 routes; SHA-256 `90d675dfdd7aac0727493bf4f38f4c9eccac6df4efe6d9f5f5857db4aabd14cd`
- Route locales: en=2426, es-419=2426, zh-Hans=2426
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3348, search=3, status=3, story=2844, subscribe=12, topic=771, topics=3
- Story routes: 2844 for 948 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ba6af20548759108a05874febbf4d3bd7e275a4ab1fd818608692f47473d81d1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `a508b0e2bcf1637606bcd5c857d7d2a7040ba894caa66bd42622135885e27bdd`
- Candidate tree: 26713 files, including 2859 local story-media files; SHA-256 `34ea5306b7862884e8a412da1bebb7a4325510ce02561236e3ac975a2857973a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
