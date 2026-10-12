# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a94bd44acbf6e3e9a6911f2a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T05:57:15Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2568 routes; SHA-256 `6e4d767fb0ade5ff844f15908485f7a3cbdaae5a9ac3c85bb59f3d28a294b3af`
- Route locales: en=856, es-419=856, zh-Hans=856
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1284, search=3, status=3, story=852, subscribe=15, topic=252
- Story routes: 852 for 284 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b5d689f1ccad539e62075c41693e581535744c4930393363c91eda7087944746`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `42d158834d124e3d37d7cfd9b51041edf6d4596baa71011b1259025861f8a570`
- Candidate tree: 8990 files, including 861 local story-media files; SHA-256 `b7c484485e6b2e060ad60847c364aa3592b6593f4780626b366ec05d4a3552cc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
