# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-508f69b29d935429b6b2fb51**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-18T00:10:55Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4572 routes; SHA-256 `9dd97036a3430de74668d6c4bbf2d288ef2d4484a8b38e1ac68a4b7c35c9f426`
- Route locales: en=1524, es-419=1524, zh-Hans=1524
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=108, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2181, search=3, status=3, story=1701, subscribe=15, topic=492
- Story routes: 1701 for 567 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `6f16edf385d22f0788f599b6875daab228b058c5b3c6064eb8dc3df0266dfa41`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8aa71c53da3633aa2d4f88d7517139008afc290c514105250037c48fe97cc0c7`
- Candidate tree: 16434 files, including 1710 local story-media files; SHA-256 `838728a361cd00bf268904f8a157bf9e7def48b0bbf431636bcd8ae9e27bef25`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
