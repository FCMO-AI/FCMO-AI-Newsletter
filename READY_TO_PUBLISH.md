# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f0a5c7edef689aa7f65df901**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T10:57:02Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2691 routes; SHA-256 `fa48824ff2d85f0fba16c7f96e601eb0aed42864facdad9cffa1564e8bc7524f`
- Route locales: en=897, es-419=897, zh-Hans=897
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1332, search=3, status=3, story=912, subscribe=15, topic=264
- Story routes: 912 for 304 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `75df22d2bf689619004b82b2f815ace86781eb68d6f177037fd29ddabaf34b19`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0612077a48beb34f3d8553cd4cc87aa975087abf3ad125b1a04a014d7237bd1e`
- Candidate tree: 9482 files, including 921 local story-media files; SHA-256 `bf5149aedb8d34be779c03edceec2182dc0da81cf27c0b7058387a7c841245e4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
