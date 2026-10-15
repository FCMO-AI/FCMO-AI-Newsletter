# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-98e8c7a2d931c9a2abc18eed**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T08:06:00Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3813 routes; SHA-256 `65c206e216cae3a906399a6ee239a201e242f9e2ec6f875b6ec32ee8602de9de`
- Route locales: en=1271, es-419=1271, zh-Hans=1271
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1848, search=3, status=3, story=1389, subscribe=15, topic=384
- Story routes: 1389 for 463 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `abad3c49cc9b837324daeeaa7e89e470a5f62123bd52cdf04a9fb988435b5931`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6845a5a13fc6180f3694adbe4c927b6da541834ea6657ee1c269f3d2830db20d`
- Candidate tree: 13673 files, including 1398 local story-media files; SHA-256 `0253d46ddb6304a9b5c371a85ba728ab7745c8696d3439fd5acb8cb663b56a55`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
