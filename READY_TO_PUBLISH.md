# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-31474162872d38d750839374**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T01:12:07Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5085 routes; SHA-256 `cf631257fc25ca92e0c22963ba5804e5b7dc158e71e189f655f224c9cafb12dd`
- Route locales: en=1695, es-419=1695, zh-Hans=1695
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2403, search=3, status=3, story=1914, subscribe=15, topic=525
- Story routes: 1914 for 638 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3525430b802013ded203e07d416db7fe68d49b4381e44547ddc355d4d2c1a167`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `23b541ef7dac8b379d87723ba7b3328ddc9f8cd15384303175fcc5d5ec5a23e9`
- Candidate tree: 18317 files, including 1926 local story-media files; SHA-256 `766884e6f288c88d453edb3129986bc91ef6f13d67d8ed02dba12dd2b08b30c0`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
