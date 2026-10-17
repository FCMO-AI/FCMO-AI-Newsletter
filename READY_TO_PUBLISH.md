# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7cbe06a281e459edd69040d6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-17T23:10:04Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4569 routes; SHA-256 `000674c7954bfdf1a66527e6d2f94b4847028b5aa834907db8585ff31063c0b1`
- Route locales: en=1523, es-419=1523, zh-Hans=1523
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=108, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2181, search=3, status=3, story=1698, subscribe=15, topic=492
- Story routes: 1698 for 566 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b4253cb63878ea86b0817b928ff8ece152fc40e290baa449578faab0c2a2107d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2a0546b40ca6586f4ae5d740bcd5fe2c92729e87214c3b04b52db3f164286e53`
- Candidate tree: 16412 files, including 1707 local story-media files; SHA-256 `fe76c9d28b127df0ec29902ac7f1b631ddaddceb52163c9bef444e0d930be0c0`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
