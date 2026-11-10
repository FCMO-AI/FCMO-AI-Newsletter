# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6a7e8c8bcc72e866bb0d68b2**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T12:17:23Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7224 routes; SHA-256 `b02a6ed18442173d8a14bc49502c9be2d69e30f83591868c51629f88ede7e7ca`
- Route locales: en=2408, es-419=2408, zh-Hans=2408
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3333, search=3, status=3, story=2817, subscribe=12, topic=759, topics=3
- Story routes: 2817 for 939 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `241eb8e1eaebce4de40cb3dcee18ea772faab00436eda70b79fba52bea6144f1`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e5c6cc3e312d8e8b59a93e2c5e7c6b102333112fb4f5d49752c90ed5bd5b9086`
- Candidate tree: 26492 files, including 2832 local story-media files; SHA-256 `94168308c957e4d2a6d94ca40d98ddf9550c74472a615d08c2bff1be18f174ea`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
