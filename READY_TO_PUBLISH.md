# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d2b93ca3bd02711491cc5d78**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T05:13:31Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5418 routes; SHA-256 `9e655b11d40ab34e93ddec4b7e30c15ccf82cab3c4e882061d066e9a5e1c78e4`
- Route locales: en=1806, es-419=1806, zh-Hans=1806
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=126, feeds=3, landing=3, legal=9, method=3, org=2586, search=3, status=3, story=2052, subscribe=12, topic=546
- Story routes: 2052 for 684 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ceb9844fc8cb31e9a5c395330cda58b44b4e00cfbf886f8d6209630fc3368fa2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8e6d39630dc9c1899fa1e610cf9465ceca490b6975faca68516cc68a6e1b3027`
- Candidate tree: 19598 files, including 2064 local story-media files; SHA-256 `381d6f100cf0fa225e69785fc3df720e11f406380de086058d2d8dca136216d4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
