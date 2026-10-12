# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-33985ab0011a283fc8b7d54b**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T08:57:42Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2661 routes; SHA-256 `bf1a743bd63dd562491fde07e2cce290b9a812aa00b9111f71bae6d331a50d7a`
- Route locales: en=887, es-419=887, zh-Hans=887
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1326, search=3, status=3, story=891, subscribe=15, topic=261
- Story routes: 891 for 297 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `290dabdd8b77da7b94185c987b16c3f8e62dbb53f3a3aeea32d79148fcb2b493`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4e0cb25a40ddc7c44b940916fd0c607edbb52c1f737fd9cb3973f15a4a5b5294`
- Candidate tree: 9327 files, including 900 local story-media files; SHA-256 `eb1f3586f97b8544771fa293265b9149dafa23b1ca4a1c08d40a62daa9405e8a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
