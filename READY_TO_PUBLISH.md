# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-ce127c24f5bef3c6c16a13af**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T13:34:23Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7233 routes; SHA-256 `fd16f253abedf3fd31fb334f40735f1b5f2396a0cbcfd2bda8be605b8f6e77eb`
- Route locales: en=2411, es-419=2411, zh-Hans=2411
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3333, search=3, status=3, story=2823, subscribe=12, topic=762, topics=3
- Story routes: 2823 for 941 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1ab697347d97c1eaa433903ea3192faf154414bc43b9ba5fdd3552c2a70ad978`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `f80b1014d87f241bd21267c0ab66318dfdd10844e275e778bae726cb29334e39`
- Candidate tree: 26537 files, including 2838 local story-media files; SHA-256 `adcf2e4bb12276dda15dd3892318b19c2fac661ec43e42aba9609992147d9a67`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
