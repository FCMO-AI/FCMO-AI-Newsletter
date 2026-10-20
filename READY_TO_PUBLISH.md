# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-dea1b3830d652a0aad821b98**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T06:27:45Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4851 routes; SHA-256 `086c6d85376ee9be3b2889972634afb2bd6fb86f1cfcf7c517d29085fce92414`
- Route locales: en=1617, es-419=1617, zh-Hans=1617
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2307, search=3, status=3, story=1821, subscribe=15, topic=516
- Story routes: 1821 for 607 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ce2bad0e09bceebfd945ad04faecc3c7b5a3d8d753eb388ec78e96b212c06521`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e97d8c65903c4f4b00637bee121577cd4edc1670eeb839d8ca5f42ffdb338732`
- Candidate tree: 17478 files, including 1830 local story-media files; SHA-256 `b0b2008981c6de1bb88d02fb9f78f089636049b1669d93db93ba9039d817436f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
