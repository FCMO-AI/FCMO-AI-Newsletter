# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fe0dbbba539d096b8d7fe4a5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T05:23:37Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6018 routes; SHA-256 `617fd398c70c4de6910a789bdbdc236575de1bd88b057a5fe586d7fe06ec9f26`
- Route locales: en=2006, es-419=2006, zh-Hans=2006
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2814, search=3, status=3, story=2310, subscribe=12, topic=633
- Story routes: 2310 for 770 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `f7fcda32aa4c5d1b497a8b13834efc1f2581d41e97afedd5d63ef8325961354d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `a67f0a34516e262fdf58a0dd7bd4d7f766d22a148a355bb2061b1e7a0be79ae3`
- Candidate tree: 21876 files, including 2325 local story-media files; SHA-256 `5614be08739a6318f82808ca67895fce5c5ff8cada37363ebbdc736d02418043`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
