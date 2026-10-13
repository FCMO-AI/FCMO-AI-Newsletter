# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-5d0953a2185e5afab8faf1a6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T14:00:26Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3045 routes; SHA-256 `15d2cf83e83e10660ec9100b01b66fecf173b40e26b75e731da22fa5561bdc13`
- Route locales: en=1015, es-419=1015, zh-Hans=1015
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1494, search=3, status=3, story=1056, subscribe=15, topic=309
- Story routes: 1056 for 352 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0e71da24f1e0da67a107a04b485834741db2488d2f7cd0656deb2b3ee8c85ade`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c2cb394c201d901057c1aa8044157056dc290b9439c724d5ed88d22a36d69059`
- Candidate tree: 10779 files, including 1065 local story-media files; SHA-256 `d762f7c2247a9b65da11d1239dd87ada0a0e6ea24faf2866bba62f22fe881e96`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
