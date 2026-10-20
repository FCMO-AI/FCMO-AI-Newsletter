# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d0aa1ae82f06e4f745ed09d2**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T22:12:26Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4920 routes; SHA-256 `489cf0f434e9cc7c6255ac2fb104291148650ccac290033bc7266f04983266f7`
- Route locales: en=1640, es-419=1640, zh-Hans=1640
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2334, search=3, status=3, story=1857, subscribe=15, topic=522
- Story routes: 1857 for 619 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `2d9905d747cc913c5eef0b53b89b0f00f16baae876a57e3ce1ba35e2191af7b6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `44a3dfa72b241e99a14efac9d5cca4cd84d17f25c8e32d87f1b34e4f087eb00b`
- Candidate tree: 17777 files, including 1866 local story-media files; SHA-256 `18f16440d46cc3104262be8793f87803fd960887f0efa1471aa2adda8a8ae688`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
