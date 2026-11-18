# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fb8f93caa8aaa796000e267a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-18T21:40:43Z`
- Edition: `2026-11-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7548 routes; SHA-256 `33a5bbd7b9a482ff8954fe77fdb5c1c689f6e9e3039514f3aadf5404597398d6`
- Route locales: en=2516, es-419=2516, zh-Hans=2516
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=195, feeds=3, landing=3, legal=9, letters=3, method=3, org=3447, search=3, status=3, story=2970, subscribe=12, topic=798, topics=3
- Story routes: 2970 for 990 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `6789822629684b77f7f9cd1938abeceb8077850d73ea408974c066d4bd6d3b48`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ada49d39902bc9c02d3ce8d03d7496e0716f568208d48c397224af6e3896bc69`
- Candidate tree: 27832 files, including 2985 local story-media files; SHA-256 `2d3be09843c48ad434ef7d2db023746c507de5e6498cb0b7e3593b8523cbb58e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
