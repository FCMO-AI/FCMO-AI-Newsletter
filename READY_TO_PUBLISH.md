# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3e54472bd3b64f7025eb9b68**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T10:35:03Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5004 routes; SHA-256 `d53580a3992251e3a033f4348a143c74cc668e382db86972fb1da56d1de37636`
- Route locales: en=1668, es-419=1668, zh-Hans=1668
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2376, search=3, status=3, story=1893, subscribe=15, topic=525
- Story routes: 1893 for 631 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `26f1a00d7f38eafbca7c2c2db8b0c9beb5bc61c2cd3d12c7742c73948546057f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `eb1e7ea120bc5ee29b8ac23927c1eadd45160f8efb1c8945beadc4d9eb4b1367`
- Candidate tree: 18094 files, including 1902 local story-media files; SHA-256 `720888bb34feb88c003e55f650351dd086d64d668cd31621852cbe27a774ede4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
