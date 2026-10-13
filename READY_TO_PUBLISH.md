# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6e9db89cb9583ec706f5c22e**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T21:58:25Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3216 routes; SHA-256 `853f07c8c140f568512f54bd45422ab5daa605e94f8bde2850168b15d99ed64a`
- Route locales: en=1072, es-419=1072, zh-Hans=1072
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1554, search=3, status=3, story=1137, subscribe=15, topic=339
- Story routes: 1137 for 379 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5b66b79f3293e2bc844e4aa4d9ff03fa672e280ba423d619b27f044f56a423ca`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `be087311a55b9202e97b63da1701dd7ab138f084ef1960735ddf5e3305379237`
- Candidate tree: 11453 files, including 1146 local story-media files; SHA-256 `957fec33db1d1a9a3333166f6b0eb7fc0a225a1222fdff9cae026e8cc5e0d93c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
