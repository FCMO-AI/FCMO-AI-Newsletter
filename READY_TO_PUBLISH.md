# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-0d4a95c675b6bd060f6df103**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T13:14:41Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4878 routes; SHA-256 `08cd319fa681c79ae858dd6f55536fc714a5466a85bdfe80b2df47f928f431da`
- Route locales: en=1626, es-419=1626, zh-Hans=1626
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=12, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2313, search=3, status=3, story=1833, subscribe=15, topic=522
- Story routes: 1833 for 611 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ca4171055c7398baba07dd74b14220c03e4aa8c8b806fb09a792fb86a9e35ec0`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `9895907adf527dc3dafd30971ba9381d6b36ad8595f24d3b131dd3a6224ec9e2`
- Candidate tree: 17589 files, including 1845 local story-media files; SHA-256 `479af4001e1e1599228e6f15e2bac58bd97df7a499f8dedcb10079676227f4df`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
