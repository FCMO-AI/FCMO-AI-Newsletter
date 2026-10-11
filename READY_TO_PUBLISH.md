# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-7ffbfedc2cb62c13abfa9127**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T20:54:09Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2346 routes; SHA-256 `9388ae88b468f9a17f5d056b0d22db9a998b93349ff92605fb37085c659dead5`
- Route locales: en=782, es-419=782, zh-Hans=782
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1173, search=3, status=3, story=768, subscribe=15, topic=225
- Story routes: 768 for 256 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `77b93ebe9e3be053b49e89c18073957b800c450241953188176c51ceb00b2596`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `9715315eed4acf8ace48bf039a189d3113497c57cd6f1433c65eef3b157bdc76`
- Candidate tree: 8213 files, including 777 local story-media files; SHA-256 `4e0adb2b3dc04f4473a020fb02c138bdaabb63cad05df9f60e90d44d8bdcd436`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
