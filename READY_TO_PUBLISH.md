# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-250349e82cdf1a44beb30c06**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T12:12:12Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5007 routes; SHA-256 `db486c94db67ee9115abe1a29cdfecb3bc3de7b46c6b49004f447099d12ecf2b`
- Route locales: en=1669, es-419=1669, zh-Hans=1669
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2376, search=3, status=3, story=1896, subscribe=15, topic=525
- Story routes: 1896 for 632 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `05578aef4307a4f5d2e41cad12b21a2aaffcb043a038383834fd4a9cdfbb29c3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ca6eb8aaf05c810a7fd147d3a87c064819d88b1a7bfe83e7def1d06acc919c50`
- Candidate tree: 18113 files, including 1905 local story-media files; SHA-256 `992f93c5e3fa8a736b9c52c077be96a2f65188dcce65c9923801630faabc0e5f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
