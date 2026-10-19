# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-2a5771c555afa2c82e4bb820**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-19T15:12:33Z`
- Edition: `2026-10-19` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4797 routes; SHA-256 `9d73438102206fa149d13d722b0ef2851de64d93b8a9ec26919b42aa65961714`
- Route locales: en=1599, es-419=1599, zh-Hans=1599
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=114, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2286, search=3, status=3, story=1794, subscribe=15, topic=513
- Story routes: 1794 for 598 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `cf83f790bf3fdb5cc3613193bb2558de4201620f6ba7273e39ed385019cf03a9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `2cd6be95fa2a810c7f7e2badb8e10e0ad0ba6dcfe2ec33eb4af48ed08cd9eb5c`
- Candidate tree: 17252 files, including 1803 local story-media files; SHA-256 `5711d1547a1a44aaef41505eed591c8362b427783e95b8d0cee8514fee9a5628`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
