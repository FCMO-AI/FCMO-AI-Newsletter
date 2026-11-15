# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fe00b52a3a67920125de95bd**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-15T20:39:39Z`
- Edition: `2026-11-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7446 routes; SHA-256 `df9cf32cd804cdeca80d591b1bd1846c629e36e042768b4049c4d76a3e91f95b`
- Route locales: en=2482, es-419=2482, zh-Hans=2482
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=192, feeds=3, landing=3, legal=9, letters=3, method=3, org=3402, search=3, status=3, story=2928, subscribe=12, topic=786, topics=3
- Story routes: 2928 for 976 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `dcc4be831e2950e9ed17c25445e33967615ad0b8b2fe290b5dd2054e3ba1bff2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `66bf7803fa762c8c81c4492b6d4c65e95cef7cff86aebb8f700cb13af64610bc`
- Candidate tree: 27448 files, including 2943 local story-media files; SHA-256 `46282d3ca23e83b7c9cdc6867716e12836a09cb3f34a692649060e4f60ea387c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
