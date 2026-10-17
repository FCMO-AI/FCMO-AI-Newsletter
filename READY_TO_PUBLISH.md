# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7de6f374f869078dabca924e**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-17T14:10:39Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4533 routes; SHA-256 `2f4a89e8bc57c31f0b5cd335449185d6ba976e00d978332df4deab6a436efc2d`
- Route locales: en=1511, es-419=1511, zh-Hans=1511
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=108, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2169, search=3, status=3, story=1683, subscribe=15, topic=483
- Story routes: 1683 for 561 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7629472dc98839a53152e72a0534a9da64d66343b81a1e0df0f516e2892a4f3a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b2671df1c30943170bcb73c4449b92abb9badba0a2bf110a06df6b3973a2a1d2`
- Candidate tree: 16282 files, including 1692 local story-media files; SHA-256 `69e86adff8f280145feafdff095f1eea7a503f9fb3a4fb83c5022a8d1dab2502`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
