# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3d02c944f32d84e9e7188e7b**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-17T08:06:15Z`
- Edition: `2026-10-17` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4500 routes; SHA-256 `56aca55e73af03c258aa576225a248c823d0932a83954ba18e83d31cdea0d5eb`
- Route locales: en=1500, es-419=1500, zh-Hans=1500
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=108, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2154, search=3, status=3, story=1674, subscribe=15, topic=474
- Story routes: 1674 for 558 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0566beafcf4cd85f879f50f2cc8922d52579a57b9db479b6ef9827d3a67af469`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `45a89264a92de38e6eecdf0cbf9395d41f62bff3f710b49b2c5814cb0ee53a95`
- Candidate tree: 16188 files, including 1683 local story-media files; SHA-256 `c6971af3dcbf0ce48dfbfb4e02ed1a0a12366aaa5f5951cf9dc084d99177a892`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
