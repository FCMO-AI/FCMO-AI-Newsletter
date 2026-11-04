# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a4327815a9f9b6cbb4fb1748**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-04T11:34:23Z`
- Edition: `2026-11-04` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6813 routes; SHA-256 `f74ec04dbb55a5da88cac07d1e00aee7444b9b279c2183b1f2d4b4e92b9087d0`
- Route locales: en=2271, es-419=2271, zh-Hans=2271
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=162, feeds=3, landing=3, legal=9, letters=3, method=3, org=3180, search=3, status=3, story=2634, subscribe=12, topic=708
- Story routes: 2634 for 878 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fd9da4373d422cace58bc3398eb83990ece33f95b0f5cdc80faa00a55247e4ad`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d11a5042ddbe6ea8bb0ba92048119dae33a7c06b847cdc246052493ffe92e880`
- Candidate tree: 24862 files, including 2649 local story-media files; SHA-256 `7c6c3f38e620dae300021c869547a5bc644694c3b82f4cea123e858a23a97beb`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
