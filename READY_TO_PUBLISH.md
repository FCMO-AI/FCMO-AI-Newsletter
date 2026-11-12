# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-310a7a04b6f33b635e4b2915**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-12T22:38:00Z`
- Edition: `2026-11-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7413 routes; SHA-256 `c93237d37288ba86a18bb78940f6dad9cc349e523dbe5c40d0544f655551b5c0`
- Route locales: en=2471, es-419=2471, zh-Hans=2471
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=186, feeds=3, landing=3, legal=9, letters=3, method=3, org=3399, search=3, status=3, story=2904, subscribe=12, topic=786, topics=3
- Story routes: 2904 for 968 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5046ce974e4ee2349d87b493c73c01946b2fb9c02f8bb1dd3d2f7df99a37600f`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `df221cb2840bf153161dcd3f6a108ef76bc7e43530d36f9b991b6a9b9f1eedfa`
- Candidate tree: 27254 files, including 2919 local story-media files; SHA-256 `9168e58dc6aa9df9ca658962e87b8df9b4afc71b58a8d3dceff159c258ed7207`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
