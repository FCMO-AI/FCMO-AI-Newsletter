# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-80c97f2bcbdb49f529373815**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-19T06:07:33Z`
- Edition: `2026-10-19` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4755 routes; SHA-256 `b5f60b54eb739e48cbd22668ae7466ddfe24209bc474fcb2c89222b13a034dff`
- Route locales: en=1585, es-419=1585, zh-Hans=1585
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=114, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2268, search=3, status=3, story=1776, subscribe=15, topic=507
- Story routes: 1776 for 592 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `de56e649c09448fc166cad7c8df2583d9302858a80047fc827033d69f8e9e534`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `07aefede11a3e3ff9d5ba093fcda5276bc8796ef2d7e016f1c48ea7504932cee`
- Candidate tree: 17094 files, including 1785 local story-media files; SHA-256 `9a19df4954aea83ffa5cf4c564cac9e6a6e233f98bf36b14b6436d9b22d6b31a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
