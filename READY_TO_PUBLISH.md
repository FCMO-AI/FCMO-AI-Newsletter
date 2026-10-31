# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-96b2fd1cb605012575e944dd**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-31T14:27:57Z`
- Edition: `2026-10-31` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6360 routes; SHA-256 `283307de514b289fef15a3c3e714c6b7d23c3d9621628e8d36059b066e2fce6c`
- Route locales: en=2120, es-419=2120, zh-Hans=2120
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=150, feeds=3, landing=3, legal=9, method=3, org=2961, search=3, status=3, story=2451, subscribe=12, topic=675
- Story routes: 2451 for 817 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `55ef312cc7a2bf5e1e4d00ef1d7c0649ea3944b83d993c483bc5c77c1b1ea3a0`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `324cb1f5f095aa3f5df3def409c67cfee0df7249c9d9e4b667d7a368981d111f`
- Candidate tree: 23164 files, including 2466 local story-media files; SHA-256 `4fc985bd81a845000f18ee9035c3eb4fb3e00e06c36441662934c37ede6398c9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
