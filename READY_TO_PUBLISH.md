# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-dc3eaa735a4f10a714e692c0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T20:58:19Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3198 routes; SHA-256 `3fc73cef7667c36e51e00e48d709f5051f4b4190d8c821b753ee49209fd6a1e2`
- Route locales: en=1066, es-419=1066, zh-Hans=1066
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1554, search=3, status=3, story=1122, subscribe=15, topic=336
- Story routes: 1122 for 374 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `24a00d1e6cb9eebe2a0363a0354087bd14f9da3034c46247bb864b3a2ae34b78`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d059add2663241acd9a426aab2ac78ddc9dd912cd70a1ccf85104fc4b90f0d2d`
- Candidate tree: 11347 files, including 1131 local story-media files; SHA-256 `484a0d56a12cbf604fd8a96a0ad89043d7e4c3b12156c5d4b8d39ba7c618f1ba`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
