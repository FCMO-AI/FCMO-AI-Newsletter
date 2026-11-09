# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-68114dd77dc2a462bb0131f6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T13:38:37Z`
- Edition: `2026-11-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7143 routes; SHA-256 `f13fcd3a32c870defffb370620ec8a8d56316807930bd0210cf26a7a8147cc1a`
- Route locales: en=2381, es-419=2381, zh-Hans=2381
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=177, feeds=3, landing=3, legal=9, letters=3, method=3, org=3294, search=3, status=3, story=2784, subscribe=12, topic=753, topics=3
- Story routes: 2784 for 928 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `6db670509cf945451e92b5a0293c5aa193cf1a833ee73a0d2f7f2980ce0e9707`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `297d64358a1964549d3083a9dadedbcba6be3954da5958937c8f672b3a452b4f`
- Candidate tree: 26189 files, including 2799 local story-media files; SHA-256 `f27df0fa8418eb79c54885de76a534c0c1c41c1094ccb78a1f1574aebcad8086`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
