# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-01473e412a0c266127d5a1f6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T07:17:04Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5307 routes; SHA-256 `83be0a4f342f38dc9b00e473757bf09369dd2ca55d267faa5bfe5a25677debe9`
- Route locales: en=1769, es-419=1769, zh-Hans=1769
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2523, search=3, status=3, story=1998, subscribe=15, topic=537
- Story routes: 1998 for 666 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ec3738ea679b64087b6c86ed6dac9bbc58305df5796ce328af846fa69f7abd26`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7507de1a4b5d1cd69f4c1eb159e45fb44b27a96d2ba607b14df539c01d25597a`
- Candidate tree: 19104 files, including 2010 local story-media files; SHA-256 `38b40c2afed490ab04017559420802038ffccf86b60bde4862fb7cce021701c7`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
