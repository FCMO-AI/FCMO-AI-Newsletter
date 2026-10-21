# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7ddabc1485748c4d72826c7a**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T04:09:39Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4974 routes; SHA-256 `e9c1cae6f3f99e49a8e1ff20f1196dcacda4074c5b31fc9d29ebcf842005e682`
- Route locales: en=1658, es-419=1658, zh-Hans=1658
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2361, search=3, status=3, story=1881, subscribe=15, topic=525
- Story routes: 1881 for 627 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `55b88fbaac04fd18a46d9085a80f34eca7b6846c4745e90341494b6118922433`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6b2f8530909305bfb62e7ab9fb92f77279a5e8dcc57c414075b2d473fcdbbd0f`
- Candidate tree: 17988 files, including 1890 local story-media files; SHA-256 `6921a4a2038c57191f33d3cf048e3eaddefb2ed65d6d6b9dd58160ece8e35ec4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
