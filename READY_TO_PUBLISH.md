# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fc5d80239d2dd664051fc621**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T01:50:45Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1461 routes; SHA-256 `6cd6038098a0bfd618bbdd64ad8a9df13de33309e395cb8af8c3c80c42061505`
- Route locales: en=487, es-419=487, zh-Hans=487
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=705, search=3, status=3, story=444, subscribe=3, topic=153
- Story routes: 444 for 148 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `9e31019b416d93a1c683b8db83d5305101676bfa546b08b1df079e0cb427dc12`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `709ab7f190b68f46f5efc147ea0252681ad71e6bf0bc8bd0eed991907a843af8`
- Candidate tree: 5134 files, including 453 local story-media files; SHA-256 `c95cdbd244776325783725a39efc632111f64f0b41b71df364a67f72bdb4f0e2`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
