# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6ddcbc3fe51a1c65dd4fec26**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-15T20:06:37Z`
- Edition: `2026-10-15` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4068 routes; SHA-256 `443cf1f51086c690817ed9c55f85c0eb633b9c5f923272511ac1d13aae6d3f09`
- Route locales: en=1356, es-419=1356, zh-Hans=1356
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=102, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1965, search=3, status=3, story=1497, subscribe=15, topic=414
- Story routes: 1497 for 499 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `cffb10b17922627e2887bd6b939150191cdd58f007cb7faee914c13dfe8336ed`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b10fc90cdfdb9d47b33125bd3968c211e9cde4f2108efda818a782e1286a6b40`
- Candidate tree: 14625 files, including 1506 local story-media files; SHA-256 `76d2b1e544e077ecc49a6b94631fb7bc0f752d05ede72922c3139306a19f2650`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
