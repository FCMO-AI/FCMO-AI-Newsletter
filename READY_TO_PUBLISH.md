# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-549b3c58732d958a372d7c46**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-27T13:48:41Z`
- Edition: `2026-10-27` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5805 routes; SHA-256 `9e0fb938f7b979883610b0f006711eea718429bd5efd4fa29ac9efad7d20aef1`
- Route locales: en=1935, es-419=1935, zh-Hans=1935
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=30, correction=15, corrections=3, edition=138, feeds=3, landing=3, legal=9, method=3, org=2751, search=3, status=3, story=2193, subscribe=12, topic=606
- Story routes: 2193 for 731 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `87adfee6394ba5824164129059567436d51c1d5bb4a953701fa414b13e8371a7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `362cfe7c7674f41f9389ee8536f17f40b193a3943fee85c5918a42a60f5f957e`
- Candidate tree: 20918 files, including 2208 local story-media files; SHA-256 `d32b780cdb2f73e19c229efe8a85fd3971b234dbabab7df8ec4cde421ea7aa5e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
