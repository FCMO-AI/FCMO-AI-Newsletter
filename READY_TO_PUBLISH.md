# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7e5390b97f5025b9aca3aeb5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-27T20:30:48Z`
- Edition: `2026-10-27` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5838 routes; SHA-256 `59750af24a043ea40d5ddf9b059e785ea286c6d927021d0efbb106b8c896caf7`
- Route locales: en=1946, es-419=1946, zh-Hans=1946
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=30, correction=15, corrections=3, edition=138, feeds=3, landing=3, legal=9, method=3, org=2757, search=3, status=3, story=2214, subscribe=12, topic=612
- Story routes: 2214 for 738 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3fa4160305951e61a5cf742ddce319fcbbe9e9ad9465698324a61d148ce1d863`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b565f8469c7c3536ae645dc6e00844479a4d68d0f22ea5bb37c859b648475415`
- Candidate tree: 21081 files, including 2229 local story-media files; SHA-256 `bef50fbdb43c7373eb2226d448f432fa3076d62e3a6380409989bb51e230f026`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
