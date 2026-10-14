# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fa6f6d8cf27b984be38ace39**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T08:00:42Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3441 routes; SHA-256 `afb8803e25e52dc366279e55d8bb5c00a002d87c8e6e94d725cd155a8e2486aa`
- Route locales: en=1147, es-419=1147, zh-Hans=1147
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1671, search=3, status=3, story=1227, subscribe=15, topic=354
- Story routes: 1227 for 409 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c97fa5d76d55d4e84d260e948e2918fe60f62883ea3fddcfccdbd33a7dff2ded`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `48fadbad7e2af46e0b4d332293564bebe7cbfa7ab71a9b8db8f203c7a0db689c`
- Candidate tree: 12269 files, including 1236 local story-media files; SHA-256 `56205bb866a99027731265c75d9cbd58558e989f161894244860eb61cdff41da`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
