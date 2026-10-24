# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4a116b28eb85e054d99531ef**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T02:14:33Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5409 routes; SHA-256 `ce6c2c72fcebdce33e8dbf4be0418fa90538a9927c56da6a83332dd46093794d`
- Route locales: en=1803, es-419=1803, zh-Hans=1803
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=126, feeds=3, landing=3, legal=9, method=3, org=2583, search=3, status=3, story=2046, subscribe=12, topic=546
- Story routes: 2046 for 682 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `899fdeddf46b5193a0b946a822c3882e1882ecf1e60bb4d72613cb0fe96035d5`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8d7575331f73ff608f41955f725449aca48c9a2a67d9a95f16619f0e95de09ef`
- Candidate tree: 19549 files, including 2058 local story-media files; SHA-256 `0a8e468e7412dea1cbe2790247288fb1b501c87f08770d53f8887a6731556399`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
