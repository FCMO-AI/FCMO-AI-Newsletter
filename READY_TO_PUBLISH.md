# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d1da31774e3d47d9d7a984a2**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T00:05:44Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4143 routes; SHA-256 `21d6c937d99a545c70491e4cba0564e626555b651a23b0d15c56c0ff0c485abe`
- Route locales: en=1381, es-419=1381, zh-Hans=1381
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1989, search=3, status=3, story=1530, subscribe=15, topic=432
- Story routes: 1530 for 510 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ecd4e00e15034a999d174599198fc74912fe07b57eebcb76d7310fb65f3bc1dd`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b7c62158c2f7cd8bdd6bbe2fd0b7c0f13040351671648398349a87df888bd98f`
- Candidate tree: 14903 files, including 1539 local story-media files; SHA-256 `6e99ca60210a78db857d6cade7dff4887abbabecb41513f4dbd61929a8b0a7ab`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
