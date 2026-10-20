# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-fbd9a2b4cbf74e9da5c3e382**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T20:09:33Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4920 routes; SHA-256 `55e68ed224a7c3289cf8b882a81a094172b6f29294833a828e350bc86b5d6159`
- Route locales: en=1640, es-419=1640, zh-Hans=1640
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2334, search=3, status=3, story=1857, subscribe=15, topic=522
- Story routes: 1857 for 619 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `edb6772f0ee3b46e877f9379ac2395eaaeccd6f398ee79448455a6e6493c9b65`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `6a425bfba250286d2e1470f2e21d438f232d456b71c2b1baf0ea82664413d0e3`
- Candidate tree: 17777 files, including 1866 local story-media files; SHA-256 `f98ae9713d05ff643e810c15c5ecc4c06bd14d8ef579ca0401be11dda0773ba3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
