# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2bbbc3161a39722e720cc616**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T00:57:29Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2454 routes; SHA-256 `ee1a8a9a68acd01d565acf99918300a420e7029ff58b333f5d280b3b2c2089f8`
- Route locales: en=818, es-419=818, zh-Hans=818
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1227, search=3, status=3, story=810, subscribe=15, topic=237
- Story routes: 810 for 270 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0f48ce1aa9db1afe3d02d2e019fad2dbe7b01a020316e9e22fee174cb941dcf3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `afaddd856fd0d1faf3b70842b5634373fbf3cf246abdc5a17268fbd53a097d68`
- Candidate tree: 8604 files, including 819 local story-media files; SHA-256 `31dc59d617f2aeddbc0d8daaeef81abe7ced3acc5e7693c3b41a62c9a6284f9a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
