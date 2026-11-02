# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a26773fb3b7243ada1ac10d6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T10:33:11Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6555 routes; SHA-256 `b21605d75a87344ad86a74053c4c9bc0eadb9c270b55105b45adf0c4872a68e5`
- Route locales: en=2185, es-419=2185, zh-Hans=2185
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3057, search=3, status=3, story=2526, subscribe=12, topic=690
- Story routes: 2526 for 842 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `7d8749c552b6e9a0a8112cc27a6c4f3f04784cb73de154a2e08b708c70810a65`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `65355f712f81653bd9ef1579a031d1e28b0ed9791fbd279775214db2bc13a5b5`
- Candidate tree: 23891 files, including 2541 local story-media files; SHA-256 `ee13c29343929cb7c648eb378fa0ab61c1163f90c2357581863727b6b8d737ca`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
