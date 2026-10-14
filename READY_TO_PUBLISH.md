# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5cdf8e8cfb1cb28bc3b4658f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T12:02:26Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3498 routes; SHA-256 `a2143d1e1380eabd5611ddd8859c58214ae1480fcfffb60c35e570def167f839`
- Route locales: en=1166, es-419=1166, zh-Hans=1166
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1695, search=3, status=3, story=1257, subscribe=15, topic=357
- Story routes: 1257 for 419 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `35bc3e315d5cc340fcffd69b8a60fea59760df07babc2b6b8bf20755ba277e80`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `a092953f3e4c5a49d6e18ee86a08c7988088290c1ed5b7ec099656e072f93052`
- Candidate tree: 12520 files, including 1266 local story-media files; SHA-256 `9bcfda131bedca872b2b054aac202e4cbae3a8b176a414d7826b9350b9e3be5a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
