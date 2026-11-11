# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fcd2b65ab932da0916c69f56**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T05:37:10Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7302 routes; SHA-256 `3eb7b12ad7e43dbfb54d17d8930775abad0c5730850260ba44a370e56d38f5ad`
- Route locales: en=2434, es-419=2434, zh-Hans=2434
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3357, search=3, status=3, story=2859, subscribe=12, topic=771, topics=3
- Story routes: 2859 for 953 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b84b889fa5afa62b304ef2c41d2a303ffc518ca22b0d403f0361828957c41767`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e56ffa9940aea08c20605a0a7ddef20f288cfb66b153d44174d7f2b50dd18725`
- Candidate tree: 26830 files, including 2874 local story-media files; SHA-256 `d4341961b11b5bdd7fdb9eee158be339916d72e7d0daad4831506d887dea6b7f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
