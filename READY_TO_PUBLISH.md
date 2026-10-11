# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-198a50a4098baca8e8649cc1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T20:11:03Z`
- Edition: `2026-10-11` (`QUIET`)

## Final route/data manifest

- `data/routes.json`: 2298 routes; SHA-256 `55209bca3406225558b1986df4f84bee6d22192a5099e5fb6242b8b8395fbe9e`
- Route locales: en=766, es-419=766, zh-Hans=766
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=87, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1146, search=3, status=3, story=753, subscribe=15, topic=222
- Story routes: 753 for 251 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `72d30ac1ad608fe464c8c019d3e045efa5a22090a7607822486732c10db7b603`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `86ac464e61f3baaf728156f3aecb950e8ba43276a24096fb2e20ca6842ddd6d9`
- Candidate tree: 8050 files, including 762 local story-media files; SHA-256 `157649f984981926e764462cd063c46d61c6f29e04f267594d175da075f0df8f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
