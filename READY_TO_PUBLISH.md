# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-60b9d601a29b4aa6bc085255**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-19T11:12:40Z`
- Edition: `2026-10-19` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4773 routes; SHA-256 `ed298a7623d04ccb95e8c7344607853bada6f94a023be73390cc44c2f0a7c838`
- Route locales: en=1591, es-419=1591, zh-Hans=1591
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=114, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2274, search=3, status=3, story=1785, subscribe=15, topic=510
- Story routes: 1785 for 595 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `55436e9da39ba80e40c95d73f172d127fa9dcbe219f5ec9e05c769c96e4f479c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `9bacd654c1d645064e7082ab44126c854961b006e9e6de9e8246fbfed309a99e`
- Candidate tree: 17169 files, including 1794 local story-media files; SHA-256 `d5a6ef762e61e70e1193525bd80793150663d54825e24618852df500b5745aed`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
