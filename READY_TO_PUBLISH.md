# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d90b2d5cbddd42952c3f813f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-18T16:41:57Z`
- Edition: `2026-11-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7527 routes; SHA-256 `3baac5c9c6253b8d806a3c13bee255c670b9d402b4f326ebeeeb97bf73ec0ecc`
- Route locales: en=2509, es-419=2509, zh-Hans=2509
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=195, feeds=3, landing=3, legal=9, letters=3, method=3, org=3435, search=3, status=3, story=2961, subscribe=12, topic=798, topics=3
- Story routes: 2961 for 987 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8418feb0d74a335379de65494ec46e8e1aabf4174256c2273dc0464cccae5afd`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7e1586164b779662851348b5410d286e819e070f9b64a4bcdfdfc6228ba24169`
- Candidate tree: 27748 files, including 2976 local story-media files; SHA-256 `d2a5dd95f342fa750deacd28ddc536b1ed9eca8003b0317cadf8e9d4f489cafb`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
