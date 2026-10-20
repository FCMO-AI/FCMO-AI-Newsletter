# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7a831729826fb953f43e3d07**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T15:09:47Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4887 routes; SHA-256 `4a2a655f50ae66968e3c4bf65afce5a287bb107e7933bb52590d0989bb3fd99d`
- Route locales: en=1629, es-419=1629, zh-Hans=1629
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=12, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2316, search=3, status=3, story=1839, subscribe=15, topic=522
- Story routes: 1839 for 613 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `aa016e5e9ce0b7dd68b7fe92148e82154e03f516a63dd25e794f0ed0bf12869f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `66e4aacf13124e6407868512c2f359a851164b9769bec021c65309627f0e8e6f`
- Candidate tree: 17639 files, including 1851 local story-media files; SHA-256 `6ff860783977d108b00511f2b06f4bfdf0f842bde751fb5172350337b6c502ce`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
