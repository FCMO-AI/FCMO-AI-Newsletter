# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2b107cc47d418726249e3952**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T19:04:38Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3606 routes; SHA-256 `23c3cc9686af5f231df8f1ef16bb11305dfa5d18f0e45c758a8f4e5dc4245323`
- Route locales: en=1202, es-419=1202, zh-Hans=1202
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1743, search=3, status=3, story=1302, subscribe=15, topic=372
- Story routes: 1302 for 434 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1ab7222e4d6a1ac82612380f7e3f21a18021cfea4debbb2de0a0f7648c8f35fb`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b86b03d63793965a8cebd6f665789eaeb5ba69f80682e447bed73cb550a6cb2b`
- Candidate tree: 12916 files, including 1311 local story-media files; SHA-256 `cc328edbd5bd5c52c843894a5a1ae892b6478a53dc158c99d1721bf8d62a0ab9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
