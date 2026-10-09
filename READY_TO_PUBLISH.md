# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f6e17ab974211e52c0e1baf1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T03:07:52Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1482 routes; SHA-256 `eea13142bf2ca45206080a13328a937de37c8ac607cfc02ca136dca7f53fe190`
- Route locales: en=494, es-419=494, zh-Hans=494
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=717, search=3, status=3, story=450, subscribe=3, topic=156
- Story routes: 450 for 150 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `82e48ddf575ee5d956186b84629ad62045ab2c08f6ad158a87c09d6271943037`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `98972e25a0078175828c6989c5d56d69ac72cd664517d8732dfa6dabb4448534`
- Candidate tree: 5195 files, including 459 local story-media files; SHA-256 `dbfc6c0ae4072c4a8abe339674a4e971c3a4fbfe0e245fb4dc0140d32caa3120`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
