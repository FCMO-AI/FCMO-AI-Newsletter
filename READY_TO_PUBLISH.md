# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-096da9a672e03f9abc7b7c11**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T11:07:31Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7218 routes; SHA-256 `e406e91792a0f0201e0ea275f18f1c262c6c1803dfa144a9e15174023be892a1`
- Route locales: en=2406, es-419=2406, zh-Hans=2406
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3330, search=3, status=3, story=2814, subscribe=12, topic=759, topics=3
- Story routes: 2814 for 938 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `15d1dc863fb9289589d4ed97105772a453cb58da9f66c48fdf0c32ed0fc71557`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f9ea8eed2e956a619e79aeeee62c3d0e52324807ffbc10d1cdbed7d50df259dd`
- Candidate tree: 26467 files, including 2829 local story-media files; SHA-256 `06c6b3ceb6e86c00391b947cc2f2ef9b0ec21128ab572cdb77c745306a5315de`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
