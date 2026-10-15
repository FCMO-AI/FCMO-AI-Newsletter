# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-537c8bd72cdaf724ca4a4b2a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T17:08:59Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3984 routes; SHA-256 `e624905ce5d6b87ed3745bfffdd21455aeba835e73083010ffc95de78af874d3`
- Route locales: en=1328, es-419=1328, zh-Hans=1328
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1935, search=3, status=3, story=1458, subscribe=15, topic=399
- Story routes: 1458 for 486 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `83c0f5315224bd99697862b25824c1c0eba9691e98764e7f4e92a599f139fc76`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b635dd009be2c496672ed79152642e0be0858486e558b0a2261813563de7505c`
- Candidate tree: 14296 files, including 1467 local story-media files; SHA-256 `4f9da05707e82188c48c304544353d6ffbcef6862b9c8517a6091e6558ec4251`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
