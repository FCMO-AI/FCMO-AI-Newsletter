# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-20be5cf5e3ce9e44ffb09cb4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-31T18:30:56Z`
- Edition: `2026-10-31` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6372 routes; SHA-256 `4652324f7621a833bcec7bcb2e79e693b16999c35a4aa872845b7345857bcf17`
- Route locales: en=2124, es-419=2124, zh-Hans=2124
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=33, correction=15, corrections=3, edition=150, feeds=3, landing=3, legal=9, method=3, org=2967, search=3, status=3, story=2457, subscribe=12, topic=675
- Story routes: 2457 for 819 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `15066769118d3684359a686170d3841850ca461fc78c9207ca197b56183c0268`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `af09b58d887b185c043fe21e7d8a8dc9d0dffd89a965d320ae24e79b16bcd396`
- Candidate tree: 23217 files, including 2472 local story-media files; SHA-256 `dcfe480fa04b8533490e54bc893ec4672c8deb2e0f6807b943b865c6b7802de4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
