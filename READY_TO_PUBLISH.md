# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b69d33c21d61da1266714f71**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-01T19:27:33Z`
- Edition: `2026-11-01` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6483 routes; SHA-256 `c74aab493d13aa2575faf99031299fa47c631478856b3d7aa823bc43cb712dfd`
- Route locales: en=2161, es-419=2161, zh-Hans=2161
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=153, feeds=3, landing=3, legal=9, letters=3, method=3, org=3027, search=3, status=3, story=2499, subscribe=12, topic=678
- Story routes: 2499 for 833 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `bace5314fc13ece0584f267d16180cc8950519edf48856f6ea28c1d52d02e6f3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `16a57bbeecd3f59eb33850c377f7a1835e3514e6aa0b8f1978fd2aea609eebbd`
- Candidate tree: 23642 files, including 2514 local story-media files; SHA-256 `31d079ba89003ecc3b8af0a9be64f59c163bff3b35dec22f0e0b02dc325b19a3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
