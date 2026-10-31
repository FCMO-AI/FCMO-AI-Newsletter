# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5356e9f767030055ec3a1ee9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-31T01:25:47Z`
- Edition: `2026-10-30` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6291 routes; SHA-256 `18dabf3d333b0c7378d5d661937a41cc85efe64b3c61601402e6f0b4e2a9fd75`
- Route locales: en=2097, es-419=2097, zh-Hans=2097
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=147, feeds=3, landing=3, legal=9, method=3, org=2928, search=3, status=3, story=2427, subscribe=12, topic=666
- Story routes: 2427 for 809 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `46115874f4fcc48b441554e7ac6ba77ac65016e91a7b4026256b5c962ac81186`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d712321b21073768c9d40708a352e02732e4b6198bff3464edae66dd92a33921`
- Candidate tree: 22926 files, including 2442 local story-media files; SHA-256 `9227b0db807b80caa98f6b20a46ba1c92a2c2811b197bdbe8df509a86d68b989`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
