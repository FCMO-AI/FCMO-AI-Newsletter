# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ed95e31480586595ad227b3e**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T08:00:06Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2919 routes; SHA-256 `0041548de3c8a25dce8ead24dc7390c0ead4ea3e817b71cdcba72cb3ebdc3cc2`
- Route locales: en=973, es-419=973, zh-Hans=973
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1437, search=3, status=3, story=1002, subscribe=15, topic=294
- Story routes: 1002 for 334 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `9c7ff20b9cc1b1dcfbbff1d7022d6eeca67c13e19fd022e4aa57c778af173faf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d22d7eb568bfaaae1344da090f05fc83fd08cb593c66000a96416544043f49f6`
- Candidate tree: 10307 files, including 1011 local story-media files; SHA-256 `6ea2a1378e0de3e43674017d8eff141ed4e41d33840bd059dedc090195d49934`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
