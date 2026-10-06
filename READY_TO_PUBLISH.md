# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e4147cb906a8e17ee13e2070**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-05T23:02:05Z`
- Edition: `2026-10-05` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 558 routes; SHA-256 `571a16b8eb1b786ce09a628ba5baf8d939284bea233c6173fe3b9cb0275dc12b`
- Route locales: en=186, es-419=186, zh-Hans=186
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=72, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=228, search=3, status=3, story=138, subscribe=3, topic=42
- Story routes: 138 for 46 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `18db0e5315b38907f7e28c0d1191ec93f6951cba4b5fc512361123288c9433a7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `32a346c35fa0b740e4cabdb108e36fc367f118b77d366eaa84ed7d0253411d4e`
- Candidate tree: 2064 files, including 147 local story-media files; SHA-256 `4f1e8b0bff65e5ecfcaca7db44bde33bca645ee638c705e3c56eac616884a41c`

## Verification boundary

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
