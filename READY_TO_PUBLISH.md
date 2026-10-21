# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-8a5984d10daed85675c53100**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T14:14:01Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5046 routes; SHA-256 `8d8676adb2692ed49f555b8cf5fc24c7be316c235df5fef839259784fed6f994`
- Route locales: en=1682, es-419=1682, zh-Hans=1682
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=9, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2379, search=3, status=3, story=1902, subscribe=15, topic=525
- Story routes: 1902 for 634 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `882f817960a0fb464598828726baefd3d1de2980b3f5b10162bdeca49d696aa6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `3117545e979d7567e6b3900232899a611cdd9e53e8dcf31c4a7dc5ad90cc37c4`
- Candidate tree: 18186 files, including 1911 local story-media files; SHA-256 `60408dbdfbbfda4e05ce84c4cbfc3e6e7061f74cb6d45902b2c12ecdc8bbb909`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
