# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-104716ca7bf70830bf839829**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T11:32:52Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7329 routes; SHA-256 `2b0ee8da29e0c395a85186d8c26b9755b6a61d0ca8b730e6107edb512bf0f4e3`
- Route locales: en=2443, es-419=2443, zh-Hans=2443
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3366, search=3, status=3, story=2868, subscribe=12, topic=774, topics=3
- Story routes: 2868 for 956 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3aba760c3a39878e126861a7f139343f59af34bf2a467ff00e28a73139025d35`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f41e5aa752ad1b219e46b3397646cba9a7af362a2ec8ca3c3fdc887a84909de9`
- Candidate tree: 26923 files, including 2883 local story-media files; SHA-256 `7cc503298f13a7de3d2208c743ae3d000566b48777eb0ed1bba006316774a49c`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
