# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-1e1bf0aa08913f5dd6474ba0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T17:13:48Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6588 routes; SHA-256 `5ecdf02bf93ce8a4d3bde22a130fbee133cc6d35afbe134fb3f42a6332471a21`
- Route locales: en=2196, es-419=2196, zh-Hans=2196
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3072, search=3, status=3, story=2541, subscribe=12, topic=693
- Story routes: 2541 for 847 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `41da8c67d1efa46dab0eb1d3ec84ac46276b53e67ad051698ea3ec051bd0deda`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `323425ad22be752d845e4ca74d530c38f2310cf64a5a7230e29a278366ea4999`
- Candidate tree: 24022 files, including 2556 local story-media files; SHA-256 `597da5275eca824a8de181f3ad543f54b75f5c53aac8ab1e0ff98a0721f8ebfb`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
