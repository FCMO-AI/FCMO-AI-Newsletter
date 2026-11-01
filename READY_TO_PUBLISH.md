# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-84ad0c340fdedf76081ed5ef**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-01T11:56:59Z`
- Edition: `2026-11-01` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6429 routes; SHA-256 `e64f2b526fa1833428f79b8eeaf928483c533c8d806043c87f89049b430b159e`
- Route locales: en=2143, es-419=2143, zh-Hans=2143
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=153, feeds=3, landing=3, legal=9, letters=3, method=3, org=2991, search=3, status=3, story=2481, subscribe=12, topic=678
- Story routes: 2481 for 827 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `faf766bb5d8a862137039ccc29c4f08fe103ad93269deb1dbeb1839bd7c9ace7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f04a39302799f143309adf6945512b4dacc476b1aec82ab64fdc232ea8b0d68d`
- Candidate tree: 23466 files, including 2496 local story-media files; SHA-256 `4702e8aa449f0802298c55d5e8354a084471ce51f0532c53aa4b2435ba142f71`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
