# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-553f08706a1eb99ac421fb91**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T13:18:32Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5316 routes; SHA-256 `b7108606119eeaedf1645b66777720b372aea43d8175cb214fc39c91cd57c79d`
- Route locales: en=1772, es-419=1772, zh-Hans=1772
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2526, search=3, status=3, story=2004, subscribe=15, topic=537
- Story routes: 2004 for 668 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c4a957e081546ef86cefdcd37cd2094ece832b02b7d2ca9dfb7d074481e6c139`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7a274a450d28f5e11a22ac07602b102daf2899442c3d7db1a79932b340430679`
- Candidate tree: 19155 files, including 2016 local story-media files; SHA-256 `913eb07b2de5dc68d8628ccb42f3a9ceb7174d8f9aa2a196c6298c08fce738e3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
