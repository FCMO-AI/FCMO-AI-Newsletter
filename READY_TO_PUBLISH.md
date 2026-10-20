# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c054775fd043cab68922a3c0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T10:07:40Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4866 routes; SHA-256 `976b3ee4828a9cd9ff2efd7f5362748c0cfa120e4ccbb98fddeb91d3d2b7a840`
- Route locales: en=1622, es-419=1622, zh-Hans=1622
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2310, search=3, status=3, story=1830, subscribe=15, topic=519
- Story routes: 1830 for 610 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d5a0e462ce100ba2a960d4e90b05555df181a0b8fbfd093c13d339deb0f5c635`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8150629d6a46c6380a8c825cb0ae1bb622dc1a82d184cf6bc8de5c6ab1167bce`
- Candidate tree: 17546 files, including 1839 local story-media files; SHA-256 `ebd481842d56cfe0d24ca1b7711a0a2c2fccccda4e8e38a47830e480b8ed3ccb`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
