# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-009e09fc12c6a9110fb00264**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-24T01:27:46Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5403 routes; SHA-256 `a474f37fc04fd1f049a2c5f5968f625fb2f2fad5bed6266f409a76d48b61755a`
- Route locales: en=1801, es-419=1801, zh-Hans=1801
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, correction=12, corrections=3, edition=126, feeds=3, landing=3, legal=9, method=3, org=2580, search=3, status=3, story=2043, subscribe=12, topic=546
- Story routes: 2043 for 681 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `5168f3513cec5e27b75b067e9f6bbd0b5391f402773f81ff31e05d0a3c9c8070`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4eaeb55f96135e24e3dbd357d7fecfb40552d0216cd90fda51943da64e61b955`
- Candidate tree: 19520 files, including 2055 local story-media files; SHA-256 `b45123de38ed35c53fcf20d6edc0d1566c4e387e5838abad6d6fffcd63d4c351`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
