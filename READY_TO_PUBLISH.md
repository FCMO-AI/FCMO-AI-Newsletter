# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-70c615955d431abddfdcd919**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T16:14:44Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3111 routes; SHA-256 `f658ad7727fe03ae5f80b83f0d5035bbd2a78e6b7ecb48caafce419c32be9ec3`
- Route locales: en=1037, es-419=1037, zh-Hans=1037
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1527, search=3, status=3, story=1080, subscribe=15, topic=318
- Story routes: 1080 for 360 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `189c9e8a44d91a6a221bc6f7c1d0fb9c603c7e119fb8c7eac6061ae9efd934a8`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c7876131d0832c5a319cf0fa97366f45ac6ec726f3d399b37b6276b6078b5546`
- Candidate tree: 11001 files, including 1089 local story-media files; SHA-256 `ed9586f1f69df8265fd6f7f3f2fd1546ee2dda89caf20045790f7f9c84764ae8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
