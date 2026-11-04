# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-cd82311a6ded852e4810c792**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-04T04:35:11Z`
- Edition: `2026-11-03` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6798 routes; SHA-256 `b1818d4daa29392775d0bb9a6956418eb53619ec4e1f550fca00ebca04bcf5aa`
- Route locales: en=2266, es-419=2266, zh-Hans=2266
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=159, feeds=3, landing=3, legal=9, letters=3, method=3, org=3177, search=3, status=3, story=2628, subscribe=12, topic=705
- Story routes: 2628 for 876 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `58d94df8ecf890c81aa8aefe72518fab7e245207d3efd1a44e668cff03a21220`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b757924f85ca81cca8611b94fff0f196633075d0bfe2f110fb3776ca5a583652`
- Candidate tree: 24806 files, including 2643 local story-media files; SHA-256 `93702a65fcaad5ccb7f901f3fe4cd27647e9a6c441ead74cb03cbbf28c26c7af`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
