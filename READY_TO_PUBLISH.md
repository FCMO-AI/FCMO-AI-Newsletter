# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2a2f70c7c291155ed050852f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T08:09:25Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5004 routes; SHA-256 `6ea6215118e83de286224486b3ff28ba86616232cbf4dab5063dfb8d1690751e`
- Route locales: en=1668, es-419=1668, zh-Hans=1668
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2376, search=3, status=3, story=1893, subscribe=15, topic=525
- Story routes: 1893 for 631 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `20ed525059cf5ee3334d0cfdfcfcf5247cc02cfe2dd00797bdad1bb58ff460d3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b97520c9e1a1ddac530cafc7a70c7d8b8d9a739c00ed771e80af77251befb898`
- Candidate tree: 18093 files, including 1902 local story-media files; SHA-256 `8dfa7ab22b4cfb59a504814bda5cddc5a72e6f6d318d29f4c3d08375c33c6a8a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
