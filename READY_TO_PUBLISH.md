# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ffacf2ea156a68cd325812a8**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T12:28:51Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6561 routes; SHA-256 `510d769330a495dbc8e2d1d2cceb99020c1c9127871aa800d4ef69135bd3c8a4`
- Route locales: en=2187, es-419=2187, zh-Hans=2187
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3057, search=3, status=3, story=2529, subscribe=12, topic=693
- Story routes: 2529 for 843 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `9d5e3e3045e7307e55db212ad9a3951e1f2cd6e10c382ca21c0807c0f64a16e9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c1542eb89493bac605988204835a45efef9d741c1c9d8d5e4af6c77128650ed2`
- Candidate tree: 23917 files, including 2544 local story-media files; SHA-256 `fe87982adf7d6343d96508515f3cd076fc70879729244e756df61bbec5cb6777`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
