# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e8ca596ddc0924062236b4fb**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-16T03:09:59Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4215 routes; SHA-256 `ae882078bc35e174e2e2a96d72eba0a87c781761bfd309d12f4524b7ea5d0bb6`
- Route locales: en=1405, es-419=1405, zh-Hans=1405
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2025, search=3, status=3, story=1560, subscribe=15, topic=438
- Story routes: 1560 for 520 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `82acb47b3a8a9bf815ba54ae1ea66a090a82cd6ba7cd2c572c760621d0ee3406`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `59ee57d1d749e136489db7701f38c26a9bd64a3d1325262b170882ae71060380`
- Candidate tree: 15161 files, including 1569 local story-media files; SHA-256 `e7dea2dba7951f7d36e6645b6a158a7a2c95d08b7c6109941a51ebad62bc8e77`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
