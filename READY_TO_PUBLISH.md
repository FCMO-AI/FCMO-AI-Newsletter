# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-1c9e010caf7d063fb994560a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T09:58:48Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2679 routes; SHA-256 `c2dfacf183fb191623bdcf88a8daa87a1b548b2f2e9d952804cce3e8f60222b2`
- Route locales: en=893, es-419=893, zh-Hans=893
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1326, search=3, status=3, story=906, subscribe=15, topic=264
- Story routes: 906 for 302 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0286129fb23445a30757c8e7bc68769fae46349db00382d47654b2e03fbe188c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b21f51a359ca843c1ea0210d37c287587b3a9e016d75254ef7fa24ca76d52fdf`
- Candidate tree: 9436 files, including 915 local story-media files; SHA-256 `b1415f1a5d18930733ef46065735b2b17d9809a86a05aa25425fe5e7475558b4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
