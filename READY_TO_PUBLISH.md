# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-9766aa52b3f4d0a2eec6be81**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-15T10:35:08Z`
- Edition: `2026-11-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7434 routes; SHA-256 `991b3ff0e9aaa5309475b0790dcdb0e63ab414a74f70e438b4a7d493967f1424`
- Route locales: en=2478, es-419=2478, zh-Hans=2478
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=192, feeds=3, landing=3, legal=9, letters=3, method=3, org=3399, search=3, status=3, story=2919, subscribe=12, topic=786, topics=3
- Story routes: 2919 for 973 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `850d8daee32168952e3fc363a0524a4cbb2c62a9b7800fe7d019adc009eb2895`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d6477da76117be8e74eec0d6ed6f97d90e8c4a4552725cfd92bbe66d49780a84`
- Candidate tree: 27380 files, including 2934 local story-media files; SHA-256 `bce1a9bb4e57afee15a5c21787b3db2a6ebe3ca60233da05564b1a8b4ef23215`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
