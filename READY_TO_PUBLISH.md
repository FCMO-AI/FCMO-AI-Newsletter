# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-387e259ffecfa830c1c0b60d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T07:01:21Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7302 routes; SHA-256 `1a336b457af8d973035f9d65f0ff2135ad03cd284935a0194f23aedc5627d2dd`
- Route locales: en=2434, es-419=2434, zh-Hans=2434
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3357, search=3, status=3, story=2859, subscribe=12, topic=771, topics=3
- Story routes: 2859 for 953 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ec845551bbf1139e23b0c7b49f780ef245a9d1b4646f061e7e2d3ad7bbbeb409`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d7de54344b1d46dedbd47383cfcd93fb07b266a7c21e12bdc63b2510cfc4a7c4`
- Candidate tree: 26831 files, including 2874 local story-media files; SHA-256 `0b2c2e8867ee775de1ee289d48b13d73393276ad2b4f4d652b27891a61ada11d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
