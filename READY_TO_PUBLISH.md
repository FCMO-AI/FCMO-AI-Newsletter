# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3690e8fbc5bc515b981b4b36**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T06:26:14Z`
- Edition: `2026-10-29` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6024 routes; SHA-256 `2516e783866288b22d7cdbbd38c17c8bf1d6883224c8a16f613dc4d684ac2b5e`
- Route locales: en=2008, es-419=2008, zh-Hans=2008
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=144, feeds=3, landing=3, legal=9, method=3, org=2814, search=3, status=3, story=2313, subscribe=12, topic=633
- Story routes: 2313 for 771 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `87ada69f97ff3d407e6d8446fb86213849dffa84cc368f66481c451d0b468a36`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `41565039fe1dc7a00852d39588a373ae276cdd9b03fc538c6973f1b1ce3d6454`
- Candidate tree: 21907 files, including 2328 local story-media files; SHA-256 `d7dc34068207d10ca85e1a9b6f760eff329b32965692aa4287697aa8af10aab8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
