# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d8656fe2e9131d819aaa847c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T12:11:32Z`
- Edition: `2026-10-22` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5175 routes; SHA-256 `a0b4cb68384388cd83c4ad75c673a0c1b5bdf733f9b99ee3ab5eb6e1e810c090`
- Route locales: en=1725, es-419=1725, zh-Hans=1725
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2451, search=3, status=3, story=1950, subscribe=15, topic=528
- Story routes: 1950 for 650 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `36b8b6a06c018fa37499738e1a855941a14d0054240309b587a57c0e1d76fea9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `0430c78949d5c052a26ba8e184c58a30becd19008da506827bc38332e67041fa`
- Candidate tree: 18643 files, including 1962 local story-media files; SHA-256 `d08cfd884e33c5c3a96fce58e6383d13f6e30d3f4de8c1bbdc18a19635217122`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
