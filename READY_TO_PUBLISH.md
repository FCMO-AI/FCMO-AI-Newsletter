# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eea6e0cceb493828ebd27d65**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-10T01:00:12Z`
- Edition: `2026-10-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1959 routes; SHA-256 `35eeef00db2adb2f050f17f35b1e6b703ef3d5c65f1c9e5dbec08575595d281b`
- Route locales: en=653, es-419=653, zh-Hans=653
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=84, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=981, search=3, status=3, story=621, subscribe=3, topic=195
- Story routes: 621 for 207 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c9dca28853a28d14c9e054d4df155d6fd8a5725663e775e75d7d8a6ddda2f7b8`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6a884350587832f7fed41ee2636e20e23640480113780f1fecff6595a4115a51`
- Candidate tree: 6835 files, including 630 local story-media files; SHA-256 `1bdefb1bc4bc81e5438b9fe869baab76073c7643bcebfbc20d57a4cb34f4be8e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
