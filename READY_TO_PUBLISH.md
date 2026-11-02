# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e2c7277ab31f5c6cc70fab5f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T08:34:40Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6546 routes; SHA-256 `0a0687982193f2e78026196b056e6990a09d9970c5a1dba0e15b858eaf27b892`
- Route locales: en=2182, es-419=2182, zh-Hans=2182
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3054, search=3, status=3, story=2523, subscribe=12, topic=687
- Story routes: 2523 for 841 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `8d1e044f5473de6b6e55265da6d7c9df41e1f7e6cffd22b5a14b6adbd0f360c2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d0327dd76e3c2b4e77f1a0a2357f3240d00dccd57c85a3fc419cd8bc5e4acb1e`
- Candidate tree: 23864 files, including 2538 local story-media files; SHA-256 `7f0fc94804ba8c310f8aedb1a0397bb4d78bae171291f6bbb44d9014a541f748`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
