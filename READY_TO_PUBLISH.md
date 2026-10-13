# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b2890f3340be27960cdd9c2c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T16:54:59Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2850 routes; SHA-256 `f15ef5b2ea86114e2a35453c70abdaf6c474cc840e62e7893d0e8bf3326c4a88`
- Route locales: en=950, es-419=950, zh-Hans=950
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1407, search=3, status=3, story=975, subscribe=15, topic=285
- Story routes: 975 for 325 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `f106fd7a5476d7ab42b18eac1841bd051ad9544ee92362c1d439ae0e4260b245`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `883ff5e09d69a6b4f35759f0d1798e98c86039b7997d2ed4bc9c96a01548b68f`
- Candidate tree: 10052 files, including 984 local story-media files; SHA-256 `7df970515f3f3930f8beffcaf2fafe4d5b024c14ee67e649396ca7b8aa6a9210`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
