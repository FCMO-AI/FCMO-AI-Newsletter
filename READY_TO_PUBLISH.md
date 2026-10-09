# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b9a72e742e63e83399e60ac8**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-09T21:06:52Z`
- Edition: `2026-10-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1893 routes; SHA-256 `5a7091d98ad5f0ced1770ceb57c48527017097e2c9400733d110815100315d6c`
- Route locales: en=631, es-419=631, zh-Hans=631
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=84, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=945, search=3, status=3, story=594, subscribe=3, topic=192
- Story routes: 594 for 198 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d5f20810678e6ec4ef7ec57be32883ea241e54f12c30348acdef7ebd5e5cd5c8`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0d42a66c324b0eabacf8246370c822d5645ec3f50adeba4c8f747f0726abaa99`
- Candidate tree: 6592 files, including 603 local story-media files; SHA-256 `81186141e6f405e342635a1aee4e234cfdb8baff523b5945aa76e2c24ad8c594`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
