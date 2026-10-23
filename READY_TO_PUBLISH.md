# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f66ea6940086edbb74acafe3**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T23:13:21Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5400 routes; SHA-256 `31f659a3887da082e501c152c756bc7611c00c9ad1ec52245ca3bcf769c29329`
- Route locales: en=1800, es-419=1800, zh-Hans=1800
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2571, search=3, status=3, story=2034, subscribe=15, topic=546
- Story routes: 2034 for 678 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `77d6a17d30af05c2505d248462f7b3e5c279dbd367699772566a33e3280567e7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `1ff65951d24d42dbe4561da5e0771dcdc5245c6fb2317262d382a8d7bbe7ae5a`
- Candidate tree: 19444 files, including 2046 local story-media files; SHA-256 `276bdd162b5f33f051c1211869fb938f6280be0de90dbad5c9f51866ecac28c7`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
