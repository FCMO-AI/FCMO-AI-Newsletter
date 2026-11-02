# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e7dd8e8a7a23796421a58735**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T14:30:15Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6582 routes; SHA-256 `3bd16ffbbf44eee5773ba1efc295bfc7f569c4bd04b2364b1130101db4a7c335`
- Route locales: en=2194, es-419=2194, zh-Hans=2194
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3069, search=3, status=3, story=2538, subscribe=12, topic=693
- Story routes: 2538 for 846 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7cb0cc78a9ed76bd0fbb0242656c014e5a4d04f2694ff47f1329077a0f7215c9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ef67e20af7dac1fca0c7182d3a89e445452923f0b78f058ac464732494452cf0`
- Candidate tree: 23997 files, including 2553 local story-media files; SHA-256 `56b9a782557b5507bf084a3ccf95833bd8f52402e659c2e80448f1978f1a0592`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
