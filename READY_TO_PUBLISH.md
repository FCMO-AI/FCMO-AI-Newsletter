# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ea54c177fd3dcb72e96336c0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T13:58:29Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2742 routes; SHA-256 `b4ca65ed20ecaa1557af0069d656caba4bdaade2ffffb224c496af7c629f9602`
- Route locales: en=914, es-419=914, zh-Hans=914
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1359, search=3, status=3, story=930, subscribe=15, topic=270
- Story routes: 930 for 310 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `cc87d2e30df9a13591c93515d39ee83b4879ae79cf0d915ba50b397883362cb5`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `121897914a2922383e478c2a251d787388ac8414a873f877b110a6f43b86bead`
- Candidate tree: 9652 files, including 939 local story-media files; SHA-256 `e498096347597e3a92838e90378ee4ffe4bae9b314ec094affef7ecbbdb03b32`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
