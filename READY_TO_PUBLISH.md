# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ab0e2bb6d1f65f944829609e**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T16:34:29Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1107 routes; SHA-256 `622dbe6deaf90894ecfba892e3818b14426a24ef33beaa6bf7c9aa9fd7ecf8b8`
- Route locales: en=369, es-419=369, zh-Hans=369
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=516, search=3, status=3, story=327, subscribe=3, topic=105
- Story routes: 327 for 109 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `12ba5d78552cf6ca44ca94fd9b1364888eadd63704ee77faae083eed57e90004`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ef4441b7997252e021d67ae3b6a8359d255aebcb63314cd7e82cffd69768ff72`
- Candidate tree: 3968 files, including 336 local story-media files; SHA-256 `3b85f59d4e3b99b8b17fb2bd2ab05c63f95c53eb3d791ff05599697ea37c332d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
