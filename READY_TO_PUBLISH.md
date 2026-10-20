# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5bfbde45a5e98065c55ea521**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T01:10:46Z`
- Edition: `2026-10-19` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4812 routes; SHA-256 `f509370f839f96dc1bc2cef44e93f2751c0cafb9c23965fb10323d54b17c4715`
- Route locales: en=1604, es-419=1604, zh-Hans=1604
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=114, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2289, search=3, status=3, story=1803, subscribe=15, topic=516
- Story routes: 1803 for 601 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ec0db5764065e8fa9a62babc3288129fb0d13f4fff8a23df59334f34416aeb11`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d76d398b66e0d40871b21ddb1e4a27a634b19e45a550580b7129c1ba3e5d5cd7`
- Candidate tree: 17325 files, including 1812 local story-media files; SHA-256 `19da4b8638682f98718e997cf7d4a16b32635cedca3311bc55c262a08f4831be`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
