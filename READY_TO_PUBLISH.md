# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-198a50a4098baca8e8649cc1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T05:14:38Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2298 routes; SHA-256 `de49e9a457f7e3cfa93082d53e581dbdb114f03307858745cf2679f1dd917ce7`
- Route locales: en=766, es-419=766, zh-Hans=766
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=87, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1146, search=3, status=3, story=753, subscribe=15, topic=222
- Story routes: 753 for 251 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5d52addf488ef9a6234a76dc8d14ce9bf26795b7a7efee66387c29c5cc6ab143`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `16eed16f820056137590c820b77b52985259fa6cddac3b590218203640b72659`
- Candidate tree: 8050 files, including 762 local story-media files; SHA-256 `a21b9eb6e3495784f49041d0a2b88b8df44c808564cf62614b081e272c319c9b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
