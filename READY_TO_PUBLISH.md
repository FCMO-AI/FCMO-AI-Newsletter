# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-498c4227bbe474da471c3a88**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T07:27:51Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5910 routes; SHA-256 `b587ff3090d2166ce1f6808a3e7d639a4941c480df117b605e47dec9953b8768`
- Route locales: en=1970, es-419=1970, zh-Hans=1970
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2778, search=3, status=3, story=2250, subscribe=12, topic=621
- Story routes: 2250 for 750 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `800fe76de9e327a87adf8084d2be3e400b3fc76cacd6f7856c7fa5bcd852948c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `136d47da2a9d0c22e4dbd1b65d0c4c79f1fe7019f9ee08372ad90d3984c0d03b`
- Candidate tree: 21387 files, including 2265 local story-media files; SHA-256 `aab3eda72aa89fbe8a8e6db3bcb9dee77e67a8725e34cfcc18a8ecb289818ff0`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
