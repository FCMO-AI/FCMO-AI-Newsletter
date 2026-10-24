# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-388d7a3de9b5ca66c8be4fea**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T06:18:15Z`
- Edition: `2026-10-24` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5418 routes; SHA-256 `6024874689556d23e6960e4069165f295c0a0a670a6b0e58ec72b953f83fbee2`
- Route locales: en=1806, es-419=1806, zh-Hans=1806
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=126, feeds=3, landing=3, legal=9, method=3, org=2586, search=3, status=3, story=2052, subscribe=12, topic=546
- Story routes: 2052 for 684 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5d0775d5845785fff8a4edb85624d6a4d050d4f057cc5749eb2a5396466efa03`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `fd63fc6c0a932f58db001b9848b72ba3ad1a0cafe8fc000f18dee0b37dce7bf9`
- Candidate tree: 19600 files, including 2064 local story-media files; SHA-256 `c2431ab24eecc7f907c5a57f3d124e60d18d3be66cbadf4ef7196697a0861e7d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
