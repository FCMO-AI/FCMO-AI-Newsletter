# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f943e94f3ca9a6e714a7bf29**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T05:13:38Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4986 routes; SHA-256 `c51d921c24a83e86fd2b57286fb5ef649672f2a4aaafd19a3d84c5bedacc8676`
- Route locales: en=1662, es-419=1662, zh-Hans=1662
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2367, search=3, status=3, story=1887, subscribe=15, topic=525
- Story routes: 1887 for 629 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `efe4edce78e01e27a09995b782533dcc05c122355094c748e9b80bd6a0be2cdf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d7bcb4639dd4626a9c68518a1bc3353ab52c3382e5c8f3b05253c83c52fb79c4`
- Candidate tree: 18035 files, including 1896 local story-media files; SHA-256 `626db4bc339585e2c2178cbd71f056f8577ea5f04b6b90ca8f3cf464abfa608a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
