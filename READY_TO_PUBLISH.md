# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-41ade022775ae71ad3099330**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-15T05:46:25Z`
- Edition: `2026-11-15` (`QUIET`)

## Final route/data manifest

- `data/routes.json`: 7428 routes; SHA-256 `718a98cb7b9658d3155151669940959aa10772a9e2c3a27e193a5cbeb52a93d4`
- Route locales: en=2476, es-419=2476, zh-Hans=2476
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=189, feeds=3, landing=3, legal=9, letters=3, method=3, org=3399, search=3, status=3, story=2916, subscribe=12, topic=786, topics=3
- Story routes: 2916 for 972 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1b3e454b58b42e22a9e7bc5e8bcf85a17563740564f9b453035625309f62a83d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `53967ff01bc8bfc4cc6f1f6610091d1a42158abcddca0daf7db7a38fdadaefbf`
- Candidate tree: 27349 files, including 2931 local story-media files; SHA-256 `f3b1a160a8b1b153e2eca2bd3c424a540da1d531a166deae2dfd9f1a44b9c27f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
