# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d301391cf957635fb5b32a83**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T23:37:39Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7278 routes; SHA-256 `81de7ebd937ff0ed9630bce83fe441147fac2d4ff183e8baff22527e182cf0c3`
- Route locales: en=2426, es-419=2426, zh-Hans=2426
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3348, search=3, status=3, story=2844, subscribe=12, topic=771, topics=3
- Story routes: 2844 for 948 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `4f9a7483b174873c3a5ab934e546270c7116ece16ea065e2d99c13097219c6bf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b31b30ca0be7d6cf6202527934b0a55a1a496929c746aa7fbeb3035897937db9`
- Candidate tree: 26712 files, including 2859 local story-media files; SHA-256 `d7842d523e2821cae23ea94f125409262007d741653e49f1373afade053135f3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
