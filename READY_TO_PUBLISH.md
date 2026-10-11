# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-198a50a4098baca8e8649cc1**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-11T04:19:42Z`
- Edition: `2026-10-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2286 routes; SHA-256 `21f93d6bc5e7a550e75a9050b62deabca8f404ce5162fbc53e2724a7b013a676`
- Route locales: en=762, es-419=762, zh-Hans=762
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=87, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1146, search=3, status=3, story=753, subscribe=3, topic=222
- Story routes: 753 for 251 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c5d7327b879b22acef77971e0fc4ad8a2a23ab3cdab6db56575b3a2177ec704a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f65e3b5c12692f9e0019b78ceb226c58265fc3de9994bc2c9fb7bd504134547f`
- Candidate tree: 8038 files, including 762 local story-media files; SHA-256 `0b29fab5dc02aee185ace08b7a8f40a4882e1dcab5e8b9153a4300604da3be92`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
