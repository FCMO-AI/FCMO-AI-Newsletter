# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a333839eef7d607a49654be7**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T09:17:30Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5313 routes; SHA-256 `d3bd2476cd936a184053b5eeef74580120d02cbc6fbd1ea0646907dd5ffaaa22`
- Route locales: en=1771, es-419=1771, zh-Hans=1771
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2526, search=3, status=3, story=2001, subscribe=15, topic=537
- Story routes: 2001 for 667 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fed643c3031309abaa75d54a18559e9994c75ff17f3f4e1b823466fb093e0881`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7c09b9642d0941420a89bdc7aa6e8f2f70679595c4abb5ec248a190d1f003d33`
- Candidate tree: 19131 files, including 2013 local story-media files; SHA-256 `fbbc364bec10c560960774e81a0bf7bdc50ec40b4ed57598ecda494934ef3ed8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
