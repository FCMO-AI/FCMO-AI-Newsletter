# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-45bc29ffbb59c07d0aec0140**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T17:59:07Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3144 routes; SHA-256 `5671cd12255cde2bd0e6ab60ccd11a60b1a85705a765eadde9b6d53edb725ae5`
- Route locales: en=1048, es-419=1048, zh-Hans=1048
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1536, search=3, status=3, story=1098, subscribe=15, topic=324
- Story routes: 1098 for 366 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d3344e4ee2c69156d780361ae515a4e886f30f51f6abd3fb14ae403a6cfeb481`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4d18d64dca5a68ff165000f0f09fa84b60abf6e9f6d335d766cfa5b6ac6492b3`
- Candidate tree: 11146 files, including 1107 local story-media files; SHA-256 `a1626349f6f15e41d5a80a2d001e7f2fcb6dccd0d672296f1f00fcb397d56827`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
