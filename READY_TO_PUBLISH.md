# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-e7bd94993254912cc8bba149**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T05:15:32Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5115 routes; SHA-256 `5f5f64a3b2f67d0c331a145d4241ffde2b13f26fdffcd91e5eb195060b742026`
- Route locales: en=1705, es-419=1705, zh-Hans=1705
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2418, search=3, status=3, story=1926, subscribe=15, topic=525
- Story routes: 1926 for 642 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `4b076ba84cc13d9101df17fd12b6da333aa4bed632739aec9b714eeae96ac000`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ed9426952de9b06873aad55c1fd8c50e0d779293e94f66ae1459932f65e8d320`
- Candidate tree: 18431 files, including 1938 local story-media files; SHA-256 `6e3a1d5e4fc6e1da3e948a84b978867e7416cfafcb5f1bcb9feae89cd9aff5e3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
