# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6be20d8bf1b8327fa05a8329**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T04:33:38Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7134 routes; SHA-256 `d5765f34380d02c7f4945177f8e40de7cd01b7e5ecd09ca72d34143e14f37394`
- Route locales: en=2378, es-419=2378, zh-Hans=2378
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3294, search=3, status=3, story=2778, subscribe=12, topic=753, topics=3
- Story routes: 2778 for 926 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ab3d5a191d88e47385a5a7a1537580834a68ac25a6ded3a74726617b204560e4`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `1ba42dd9ad1a528f17a1d148cc529dce1d2004e3b3e2fbf5fa397200f017925c`
- Candidate tree: 26135 files, including 2793 local story-media files; SHA-256 `3050bd97fbfd91abc2394b48f038f67a1d4f1f7322d5456f4f6abeeff1d28ef3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
