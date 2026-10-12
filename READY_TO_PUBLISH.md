# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-71dafbe221dc9efd85e8eb13**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T06:54:16Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2604 routes; SHA-256 `41d4a1b7a2446a0566887760562a5c20c1626b3c709c690415c14c9df2b19b07`
- Route locales: en=868, es-419=868, zh-Hans=868
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1299, search=3, status=3, story=867, subscribe=15, topic=255
- Story routes: 867 for 289 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0565a6f6d88bdc6efc50924e04fe2e4771c371dc07540e7445336049299e7f6a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `261d8e2e864d6f09fba74485cc53c0aa7ef04e004a6063f6fc5f3ca3eab2c61c`
- Candidate tree: 9125 files, including 876 local story-media files; SHA-256 `0c610104491e2b1b0a517183b7c404dc7f5725a975bf5b72797b7483047e8aae`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
