# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6d1d2205d866e7e65fd09d01**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T15:33:24Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5325 routes; SHA-256 `e8b1334ac1aaa5aa919667c8523cea64a3bbceadb7cb49368c8004c20d6417b9`
- Route locales: en=1775, es-419=1775, zh-Hans=1775
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2532, search=3, status=3, story=2007, subscribe=15, topic=537
- Story routes: 2007 for 669 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `469a68f2e67308a23e5be8ecef30c3cc54bb88c121907898bb7dafb33f31306a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `33533c3b8f37138d4cd4c66f92d68d83c59990e8656338363aecba1d8d4b74ec`
- Candidate tree: 19187 files, including 2019 local story-media files; SHA-256 `c8350f65cec644a73a303035af2164df58a06e73833be0dd3a4a17266532f2c7`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
