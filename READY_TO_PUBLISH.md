# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-b515ffac38079916eed14181**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T15:06:56Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3582 routes; SHA-256 `a2119a09b48ebac16488a471c3c02ed499804f97677825ef27af4a6b01131b09`
- Route locales: en=1194, es-419=1194, zh-Hans=1194
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1731, search=3, status=3, story=1290, subscribe=15, topic=372
- Story routes: 1290 for 430 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fdad07b4dbfd8f133affbf4460cf628aea2c68d689d4784acf3b6ab7ea967269`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d5d5ba9294f2cc2db131f13144b5466d2bb697a3f65ef0964ae9a7b767fad4a5`
- Candidate tree: 12821 files, including 1299 local story-media files; SHA-256 `9768ba9d3cf6246a164aa8c345b760e3f5a3a35cb87e626d40cc06ad309ee0a8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
