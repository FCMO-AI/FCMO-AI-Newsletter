# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d2ffe3f7e38100e1af5179e1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T00:08:18Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5085 routes; SHA-256 `2de2af0d9f0ec13c73c4075bab13311f80875edbf7744c3dad93a29a45ebb9e3`
- Route locales: en=1695, es-419=1695, zh-Hans=1695
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2403, search=3, status=3, story=1914, subscribe=15, topic=525
- Story routes: 1914 for 638 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `bad9210b928d86954d5aea901d1a533c036969fa8760ef82bb8d91f2c2c5c36d`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `42cb8dd564b62a70e7036fec4e81937094ed7fd530af516b1a48142244a2fa17`
- Candidate tree: 18316 files, including 1926 local story-media files; SHA-256 `614204fbc4e746ab3e448514d109e5049a19cf64604d702c6853a4c88c45266a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
