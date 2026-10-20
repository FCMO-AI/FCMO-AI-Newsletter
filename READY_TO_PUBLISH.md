# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-9fe3ce65a5bfcc7a77e8ddf9**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T16:20:54Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4890 routes; SHA-256 `90f879f2f2d1b51c7e132cd42e352e8b319e5a21b37e15c1e1d5236d1e6321ab`
- Route locales: en=1630, es-419=1630, zh-Hans=1630
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=12, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2316, search=3, status=3, story=1842, subscribe=15, topic=522
- Story routes: 1842 for 614 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `de9f23a09c29c9cc2cd0c21be6845d053019c55f57285231ae37967d549f546e`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `60816fe7535eefaaa46212b1dac4408b4b4754cb55465be3ed7af902477a7717`
- Candidate tree: 17658 files, including 1854 local story-media files; SHA-256 `18adbb29d0ba48329a0103baa6fd256f3f27333a30bee3b95b8f9393282e45c9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
