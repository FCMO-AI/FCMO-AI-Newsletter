# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5e9b3c3b2696313b331eb814**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T00:33:52Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6000 routes; SHA-256 `d612fe41da9409eeb77d2facdb3fe0d0eb61b128b48355a4a7f8d7f2924aebc6`
- Route locales: en=2000, es-419=2000, zh-Hans=2000
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2808, search=3, status=3, story=2301, subscribe=12, topic=630
- Story routes: 2301 for 767 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `9718bfc4c645a789660bdc1b9734f1f85fb8956888b6e6e657fb5c6d409cfd59`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `dd8e16c7739cc61e02310128c84d5a7e1e491061b9030da3b83a63996102fcec`
- Candidate tree: 21799 files, including 2316 local story-media files; SHA-256 `f92e83a6312a17c706270876644700fc92bae2d8fe54af23a68aef91967c2184`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
