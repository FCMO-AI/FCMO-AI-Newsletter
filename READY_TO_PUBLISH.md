# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-60b018570cc19e7241aba41d**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T10:01:50Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3468 routes; SHA-256 `7da49aa2bd61dfc2d07e188d92d2fe80ae7f9da1d0b7e4b0a917c3ab1873c08f`
- Route locales: en=1156, es-419=1156, zh-Hans=1156
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1683, search=3, status=3, story=1239, subscribe=15, topic=357
- Story routes: 1239 for 413 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `45989349b569d57dbedbb4d268d1b1de270e4d89d9100d15f1fea33a9a8f5240`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5787f471019fd1cefb60e5e774dbb2183e3037e4955a9d9e3c78518cd5f25e51`
- Candidate tree: 12375 files, including 1248 local story-media files; SHA-256 `d19105a33e80cb292d150031ff481406028bf1f21782adcc84c1bdf567347179`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
