# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-05b562c95512464bd4d2c3e4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-08T02:58:37Z`
- Edition: `2026-11-07` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7119 routes; SHA-256 `ee09b8ca9146f7497eb6ee8da8f84bd8cd587f1a3214d1e928ed7fa72e1a0ddf`
- Route locales: en=2373, es-419=2373, zh-Hans=2373
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=171, feeds=3, landing=3, legal=9, letters=3, method=3, org=3288, search=3, status=3, story=2772, subscribe=12, topic=753, topics=3
- Story routes: 2772 for 924 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5d6681f0debca011d60bb9b8ac2da23fa7e4eb6da5d057ae8d2479fb99d13275`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cec59006535057cac0b15f9d6424b986341ec24dfb2dc6122a940352754d09c0`
- Candidate tree: 26072 files, including 2787 local story-media files; SHA-256 `3baf23a8d88453492a7bd00afefc3b8cc4794d0648502031e79f58e1d0cb7c90`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
