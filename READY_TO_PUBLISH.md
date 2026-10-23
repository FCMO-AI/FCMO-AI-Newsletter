# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-22a025e76b12c438c7114f04**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T22:17:37Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5388 routes; SHA-256 `61b864b710c2058a16d529129f190ecd3fe956df5872ea123c51eaf98483e7af`
- Route locales: en=1796, es-419=1796, zh-Hans=1796
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2565, search=3, status=3, story=2028, subscribe=15, topic=546
- Story routes: 2028 for 676 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `70f7751eea70e365199c570191c42d25b0a135c46ff9d0806b7156452567f9a0`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ea557db90204efaea74ca6d414a4fc0707972bd73e0e4761003333cae1dd083d`
- Candidate tree: 19393 files, including 2040 local story-media files; SHA-256 `051ffeb06d6d41e50118eeffcf81e95c683f1cec77f9f3ca905580d3c44c6d2c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
