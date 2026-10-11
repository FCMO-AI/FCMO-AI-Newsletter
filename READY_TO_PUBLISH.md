# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-39542daf19a221a2af400e1a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T21:52:00Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2361 routes; SHA-256 `171807942794a1fa2b5a1533f918951d54c6eec2d1e0d9798624c0f9fc2394ba`
- Route locales: en=787, es-419=787, zh-Hans=787
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1182, search=3, status=3, story=774, subscribe=15, topic=225
- Story routes: 774 for 258 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `375d0c433037ec42c0258e3d710c23a143fad74867c9dbbae6af97555f318e67`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3b52b1cf0cc9b409a213631aaaaf385701d4b64a8169fb25ac1de73121249edb`
- Candidate tree: 8268 files, including 783 local story-media files; SHA-256 `d3424696d190b21e7595759e2a64aa4aff8d3e690405994cc54aa6fdd906cd42`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
