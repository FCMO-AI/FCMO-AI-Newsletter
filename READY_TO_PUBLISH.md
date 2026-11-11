# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ac9fdbdb51f2a906eb4fee44**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T22:48:51Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7377 routes; SHA-256 `3dbdab5699e29eaef2849cdfb433a3b4effeba1bbcbbdda6aa0677c2050e6bab`
- Route locales: en=2459, es-419=2459, zh-Hans=2459
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3384, search=3, status=3, story=2889, subscribe=12, topic=783, topics=3
- Story routes: 2889 for 963 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `3742e3ada394d6efcddbb4968b0b90fb0ab5e6624b071ad64cd9e9d7a6c4fda3`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d8721f8a1b13db349c9c8d83cc7f7ad07e4a0e0de579c5c7fe177ca820abb9c0`
- Candidate tree: 27113 files, including 2904 local story-media files; SHA-256 `90baacbf4861ecc9e23018d80a41fd417cd921d0ccaef31cf86f76eb178e664b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
