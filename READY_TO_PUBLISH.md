# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ca1e0123f2ad5aded9e9a314**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T17:32:34Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4893 routes; SHA-256 `1503e13fc1ba4025c8c2fe4ce717b1431d2a6e4bed0b86edbfcfd1d5f551e2ab`
- Route locales: en=1631, es-419=1631, zh-Hans=1631
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=12, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2316, search=3, status=3, story=1845, subscribe=15, topic=522
- Story routes: 1845 for 615 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `57264085ad2b28a14da5192e0401ae93669cda39331a3666f93d041aeebac01b`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7417f612e4a7951d71bbb25d48bdc5dd058e27e39078924dd382398e2576f8d3`
- Candidate tree: 17680 files, including 1857 local story-media files; SHA-256 `29c0748209612ec2aa53822386efe47997358d98a7c48368482e4f9e2a6a93f1`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
