# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5673309869c91ac06130da25**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T02:04:55Z`
- Edition: `2026-10-27` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5868 routes; SHA-256 `29911908841a9ca10a0fa042ab427251458709527fdb8c3fcaad47f631bc603e`
- Route locales: en=1956, es-419=1956, zh-Hans=1956
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=30, correction=15, corrections=3, edition=138, feeds=3, landing=3, legal=9, method=3, org=2769, search=3, status=3, story=2229, subscribe=12, topic=615
- Story routes: 2229 for 743 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `645320111dcc710be484208b88450a76caf010c087c4c622dc65cb71a1bd6b52`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `442291e948f7660f09c3293b2cd2b312232102a8e31fbb002a6ab52027eafbae`
- Candidate tree: 21209 files, including 2244 local story-media files; SHA-256 `7980f317a7b383386a36de18475b5d5f9a6f0d0fe36b53271d8a2bc8d3cc7a2a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
