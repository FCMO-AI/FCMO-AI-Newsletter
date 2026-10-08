# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-faacf517af0f353a4938b956**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-08T20:48:43Z`
- Edition: `2026-10-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1260 routes; SHA-256 `836f476e11265a1179bc2d36f7d14ddbb7b2223c8d04ea9bfad1e336e9d2e75c`
- Route locales: en=420, es-419=420, zh-Hans=420
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=81, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=591, search=3, status=3, story=378, subscribe=3, topic=132
- Story routes: 378 for 126 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c6b48d05caef13aea1a2bb7b44e16c381cb02f296a9eee7bfc045b676580e1c5`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2f7253867f2f93c32e84f1e3cd3ecbebed49fa5f77dff491e6c43d8250160810`
- Candidate tree: 4468 files, including 387 local story-media files; SHA-256 `ce72d01f731b89590640b13e96eeb826d8229ad3ddc1ca42751f6b8e6a09c687`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
