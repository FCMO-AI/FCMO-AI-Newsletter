# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-4eebaafe75dcafe207547516**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T12:26:59Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 906 routes; SHA-256 `0c77203e345f6bec8274f38f809a325bc28c45fc3454a26d825491012f104143`
- Route locales: en=302, es-419=302, zh-Hans=302
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=414, search=3, status=3, story=258, subscribe=3, topic=75
- Story routes: 258 for 86 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `4984140c152422b0f8ff6e9292a6f5f9b9e209d450e22abfd11540d1fa0492a0`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `9ea3a0822c1cd8b83e6657781134974eb3fd26eb9c5391f68cd86ccb8640aa54`
- Candidate tree: 3199 files, including 267 local story-media files; SHA-256 `c6fee22fdb47eb7953ee2db0661fe6a9a56d8d3eaa972dc1e51d09040b71eced`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
