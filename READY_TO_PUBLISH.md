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

- `data/routes.json`: 2286 routes; SHA-256 `024823e051812d94a76c8d9900f1a883c4f8425cc3cec9da0ba89f33b399accd`
- Route locales: en=762, es-419=762, zh-Hans=762
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=87, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1146, search=3, status=3, story=753, subscribe=3, topic=222
- Story routes: 753 for 251 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fc63fc6596c31e279f5f6d285b096fcf45c087fbb4a4931b50443358a7798426`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ed8e04ed374bfb3a6c9bea720bd00c45a5ea68865d85cfd505a508a551c86b1b`
- Candidate tree: 8038 files, including 762 local story-media files; SHA-256 `269890eb2aa101dc3deee31d710590b1e43943599e2b181627853bfc9edd5b75`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
