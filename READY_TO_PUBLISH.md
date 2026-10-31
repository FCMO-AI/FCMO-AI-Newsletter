# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-675a4b6b72bbdf87ddc52463**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-31T03:27:32Z`
- Edition: `2026-10-30` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6300 routes; SHA-256 `1edbec61d3f1f847325edc24f4a150602b2b3247f897b17ad9e0173232712b2f`
- Route locales: en=2100, es-419=2100, zh-Hans=2100
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=147, feeds=3, landing=3, legal=9, method=3, org=2928, search=3, status=3, story=2436, subscribe=12, topic=666
- Story routes: 2436 for 812 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `50f8ccea76fbda18b1bb7338e73b95e1e707083825e8ea30a101f91610876712`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f4ddf9c330fe4044201e15905fa3d137894a2ac35d0a9cc5bf561edcd477567b`
- Candidate tree: 22994 files, including 2451 local story-media files; SHA-256 `07efb22125cd5ddba849348b2c57f270ff778b482851129c675c05e59feb52c3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
