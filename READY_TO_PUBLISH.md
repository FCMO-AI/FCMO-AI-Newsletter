# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-78e4dcc219c50441fe9d08b4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T11:03:53Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3861 routes; SHA-256 `17e8d5200745c39c9454dd7b20a674b23b54a03b80fd1a0fc5f0163cb1167c17`
- Route locales: en=1287, es-419=1287, zh-Hans=1287
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1878, search=3, status=3, story=1407, subscribe=15, topic=384
- Story routes: 1407 for 469 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `77905acab076da545e16fdf67532afc9a4e6603f821ac111724dd22bfbef0304`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2e96734ed7c20a816384d80ed99d91ff0d14e35b73a7a46bb897c048cd6da71b`
- Candidate tree: 13843 files, including 1416 local story-media files; SHA-256 `d83e10bf4a820685ee8c9645f575dcefe57f42adb980cec9a178b892e4e983a5`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
