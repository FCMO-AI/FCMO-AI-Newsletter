# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c1ccc6b802344f6a146a55be**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T09:33:11Z`
- Edition: `2026-10-29` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6042 routes; SHA-256 `3e40d2afe50858d8c6ee5736cfa02523ece3d151df9dd821c351cf0323c33850`
- Route locales: en=2014, es-419=2014, zh-Hans=2014
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=144, feeds=3, landing=3, legal=9, method=3, org=2823, search=3, status=3, story=2319, subscribe=12, topic=636
- Story routes: 2319 for 773 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b5a1a38e721a33c5d97f200cfbadfb39efb41d2009a48dc42ee3f7cb4bff4340`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f7415433c051e8818d291dc9b413bd94472f9dd4bb65a4126e352b9f8d14e418`
- Candidate tree: 21969 files, including 2334 local story-media files; SHA-256 `34c07180065301ff7645b70601ea6915da9d01173ab79968299dab7520a4a87f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
