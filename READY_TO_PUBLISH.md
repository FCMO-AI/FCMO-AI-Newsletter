# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a9f5083017c794af1339933c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T22:53:16Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2376 routes; SHA-256 `af27b8c2131477357441c8063b196e322d595118492dbac6ee72481c18baf29f`
- Route locales: en=792, es-419=792, zh-Hans=792
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1185, search=3, status=3, story=783, subscribe=15, topic=228
- Story routes: 783 for 261 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b64c98bb7ab95e024abe306f9a2beacc95d64a81d0569b73639d6c8f6cdedf1b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `60fbd2228da28783f39131bf8cb3afb2e687a63dbaf1578c60adc90999a110ea`
- Candidate tree: 8340 files, including 792 local story-media files; SHA-256 `892cc9c85d9961be77c250dd00d458971d8d9003ec4238e4d8f74308a25ac2df`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
