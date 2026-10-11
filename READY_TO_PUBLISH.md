# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-198a50a4098baca8e8649cc1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T00:52:00Z`
- Edition: `2026-10-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2286 routes; SHA-256 `49c86120c360f9193ce5cb4e14bafc7e37c2fd5fc6fc51c990c9d15383c595cd`
- Route locales: en=762, es-419=762, zh-Hans=762
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=87, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1146, search=3, status=3, story=753, subscribe=3, topic=222
- Story routes: 753 for 251 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fc63fc6596c31e279f5f6d285b096fcf45c087fbb4a4931b50443358a7798426`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `12f414bd947e11cc43e50015a599b9c0266bcff7ee9f7d9f7577258c24f0308b`
- Candidate tree: 8038 files, including 762 local story-media files; SHA-256 `1ec581bf4968c2bc8abb3e6d7ce22315308895017e5415303f3c40376e5dc889`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
