# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-bb70fe3a5dff74705ac45052**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T03:00:22Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3342 routes; SHA-256 `e38cd776832826f1b9f9f79fd957ab8a7639dedad735cb7850a88679d44b2df7`
- Route locales: en=1114, es-419=1114, zh-Hans=1114
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1626, search=3, status=3, story=1182, subscribe=15, topic=348
- Story routes: 1182 for 394 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `bc3adfd3d97be5437a183d1c659519542f061361ed8c862241f4ad4fa9b2b010`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `edb0836c39f630062182f088bcca44b459c03074d68bba7bb2c20754418d40dc`
- Candidate tree: 11876 files, including 1191 local story-media files; SHA-256 `6630698b51c3127252f4d5c9be44d41b54a9912ea8a05e2ed829097701e7e189`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
