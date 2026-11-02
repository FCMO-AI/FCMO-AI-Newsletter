# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-22cada039962e1bef4b77424**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-02T21:38:56Z`
- Edition: `2026-11-02` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6612 routes; SHA-256 `7e68caff5e2e81b55ebacbc8d60a6f35d4deaaeca8cd32f89b55dbf1b2401bb3`
- Route locales: en=2204, es-419=2204, zh-Hans=2204
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=156, feeds=3, landing=3, legal=9, letters=3, method=3, org=3087, search=3, status=3, story=2550, subscribe=12, topic=693
- Story routes: 2550 for 850 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `4835eca556c32aa43e81f8be4720740ab8f0645867b4b1d26429a4e9fdb71c75`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3a288f9aa6ec1daadc3b8204cbf014f463d4429307e555d29424b038f0b064dc`
- Candidate tree: 24107 files, including 2565 local story-media files; SHA-256 `8b03e968c8cc4a7c30e4c6e76db95c71260b592349b88acdb7290bade8fbe343`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
