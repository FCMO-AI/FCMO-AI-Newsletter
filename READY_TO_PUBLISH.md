# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-028a6d7a4f9c906b116ced27**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T18:49:59Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1173 routes; SHA-256 `b4849ce91c99edb123b2a23b2fcf74490425895c397459c25acf7ba8cb7635b6`
- Route locales: en=391, es-419=391, zh-Hans=391
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=555, search=3, status=3, story=345, subscribe=3, topic=114
- Story routes: 345 for 115 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5b0806fccf0d2353fb876ce50dbecdd0cfbcc9604f31defb6c13a4c4ecaac597`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `fbf3a95ef0d0896a434722bc012e4be28fe83a35f6b4b1aaf4bbf17e9c2d48fc`
- Candidate tree: 4164 files, including 354 local story-media files; SHA-256 `11eaeb5192bef44839756d5ee32429d9498b8186e0279eea0f6591c0eb09f113`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
