# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e1ad172f59d478256a88c7d3**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-29T04:20:13Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6012 routes; SHA-256 `dea7b7a7403e332543debc1ee13cea36830f3cadc15edeaf54d3e71ef94c0b30`
- Route locales: en=2004, es-419=2004, zh-Hans=2004
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2814, search=3, status=3, story=2307, subscribe=12, topic=630
- Story routes: 2307 for 769 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5d589636f6b898dc946ec309a2a2a50aff4b076200cde99df6bb3a9091af5ae7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `735fed5c0a8474f866591568595b9565ee6edf62a483eead0fbd9eb7e54d170c`
- Candidate tree: 21851 files, including 2322 local story-media files; SHA-256 `0019fa545d37d23fc725f3e253e1d6d4f8d3631d38cc6d081b04f9e972be0fed`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
