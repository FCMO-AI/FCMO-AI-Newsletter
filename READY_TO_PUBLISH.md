# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-594b0876243266b5fd1a05e5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T19:13:27Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5349 routes; SHA-256 `dc24c67b35d0ac50dad61c98d0c44c3558ffa7066626be49a44de457e6ee51b1`
- Route locales: en=1783, es-419=1783, zh-Hans=1783
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2544, search=3, status=3, story=2016, subscribe=15, topic=540
- Story routes: 2016 for 672 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c572766a7463eb2f37ef3b468bbb2a7850368ec34b691f51d8f011b7d2be1a06`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `bd89d4d5b9ca074f5575f82b3db9d0e6f12fd0661a71022a61df8a0c155f05df`
- Candidate tree: 19274 files, including 2028 local story-media files; SHA-256 `82749a506264aacdd8272ff4234f65e2e3568ecc94ab2f654990aa8483ca3a10`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
