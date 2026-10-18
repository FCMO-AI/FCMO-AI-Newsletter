# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-933f975acb8d36940b8454f1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-18T21:00:27Z`
- Edition: `2026-10-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4695 routes; SHA-256 `259018496b90404ef0682f9dfbad8eab9d703e0bb6f38a97e877cfda63b17511`
- Route locales: en=1565, es-419=1565, zh-Hans=1565
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=111, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2244, search=3, status=3, story=1749, subscribe=15, topic=501
- Story routes: 1749 for 583 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `69d212ca75fcaa43daf6d63c2f1aae901cdcc5e2dfe01df831af7e7896ef36fd`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5e3de07ca3292e456507adb3df9be3c96dbb972d762d9844de561fa766ee3195`
- Candidate tree: 16860 files, including 1758 local story-media files; SHA-256 `9db81097b2529fda95504646ec0032053addb25bd6dd9a229c622dc0c6121478`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
