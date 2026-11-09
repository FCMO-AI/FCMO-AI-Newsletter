# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-71950c16b55f9fe3b914c94f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T21:33:46Z`
- Edition: `2026-11-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7164 routes; SHA-256 `4f27b7913af1b5ee48d9493e8c2e006935a717637ab7503c28c3a0c56b545cac`
- Route locales: en=2388, es-419=2388, zh-Hans=2388
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=177, feeds=3, landing=3, legal=9, letters=3, method=3, org=3303, search=3, status=3, story=2793, subscribe=12, topic=756, topics=3
- Story routes: 2793 for 931 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `53d722d9575475c4c9f08ad262e93dd902849f92167d30a07fd62add7e0160ae`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f7487f70fdf27c173f619a9172fb2933f366f8bf89f0ea942e8c1bf64450c729`
- Candidate tree: 26266 files, including 2808 local story-media files; SHA-256 `9a03986dcf8693ef9ab3d415b300f96b6e15df5214ec2d9fa28c3571351dd2dc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
