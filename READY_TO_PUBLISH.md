# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-334e55b27ce17cc72cff0d60**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T06:03:21Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3390 routes; SHA-256 `8a874e9ad793948a3101c744f4af8d552110b37782f7ab70a3404ece7631a51c`
- Route locales: en=1130, es-419=1130, zh-Hans=1130
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1647, search=3, status=3, story=1203, subscribe=15, topic=351
- Story routes: 1203 for 401 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `de25c2de909e077267d57d6302b9bd4bfef2696b82da45d59db6ee95fa69b778`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `1ba8dbd7bed6a60b0d99577fce082b4bee758f198db11cb43f7c7de1effecdc6`
- Candidate tree: 12057 files, including 1212 local story-media files; SHA-256 `1bebd6247c02b9ab3342241252c96be059a9641483b428dcc1c910ea8a63cf41`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
