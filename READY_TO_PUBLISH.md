# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-443cd1cc00751f58a6138ef0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T10:32:56Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7119 routes; SHA-256 `8e76d8c9b02b12e6f98a5e36b7f1eeedb8a22d291445f7fe413ae817f2986c38`
- Route locales: en=2373, es-419=2373, zh-Hans=2373
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=171, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2772, subscribe=12, topic=753, topics=3
- Story routes: 2772 for 924 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `89ac902ef3d8f839d7ca5e004bd024bc08263c6a9f1986064d32303479dfd594`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `afe89ba42f92f1af87d863370ab9c2289bff789dea23107b656d9b57e4c67cf2`
- Candidate tree: 26075 files, including 2787 local story-media files; SHA-256 `dcec183373b527721c71cbde00980894bf05aa41869d8800781c07636e302819`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
