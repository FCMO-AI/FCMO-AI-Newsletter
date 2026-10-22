# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c55623a1d93a3afa375191e5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T09:13:09Z`
- Edition: `2026-10-22` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5163 routes; SHA-256 `e8e18897df325a20395de293771c3a76ec80b077e81baaba9439c85bdc8b0068`
- Route locales: en=1721, es-419=1721, zh-Hans=1721
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2445, search=3, status=3, story=1947, subscribe=15, topic=525
- Story routes: 1947 for 649 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `951b9e82c1cdfded7ceeade0a19f81b5f47ebfa40bbdf8fa02476c83d0c3d536`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6ed68f95f7c6c7c62bcfec578b0fbf6fd82320e8aad95733c80ebff00e2119cc`
- Candidate tree: 18610 files, including 1959 local story-media files; SHA-256 `b3a1b00d9204aff36f713d4f88fcefec5afbcbb50e0249df86b9f9cfb9b1b2af`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
