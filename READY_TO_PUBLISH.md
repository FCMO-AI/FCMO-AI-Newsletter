# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-663668539c29040f79f9161a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-30T23:31:32Z`
- Edition: `2026-10-30` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6270 routes; SHA-256 `d850095ad330c316b551291c12ceac4981c56f8ccf2fa6ea99390be3b68ac564`
- Route locales: en=2090, es-419=2090, zh-Hans=2090
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=147, feeds=3, landing=3, legal=9, method=3, org=2916, search=3, status=3, story=2418, subscribe=12, topic=666
- Story routes: 2418 for 806 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `09b72613dba8085be3d59393014eea8efce6a14bb5fdf7e4bc3d125a56d00a1b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b94148f723ede76faaa81beca9214b8c1f490130211a4937e78359c284f6a042`
- Candidate tree: 22846 files, including 2433 local story-media files; SHA-256 `5c0cfef0911d382d5669e928e0ed7c4a6aa3b9e04d206c70fd9e40a663c2ae2b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
