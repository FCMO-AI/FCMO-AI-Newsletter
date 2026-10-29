# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-bd6b37e2e36c257613cf711e**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T03:27:37Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6012 routes; SHA-256 `89e7964b58b9ec2a2bbe84b3140f3a67766afa5ed8fdfa25ebc6e62bd5b177a9`
- Route locales: en=2004, es-419=2004, zh-Hans=2004
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2814, search=3, status=3, story=2307, subscribe=12, topic=630
- Story routes: 2307 for 769 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c910679b66fedeb1e0dd87383031f246847a7a5f3f1244d5cd90301db827d51e`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `998d12d3b57628496323f7dd2d9e6eeb845e920f2cf935db93b5cf1bfc8d4e4f`
- Candidate tree: 21850 files, including 2322 local story-media files; SHA-256 `22f576d95fc92ab6327129cbf4b6835a7e24a123005a4ca9a560496db6252a34`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
