# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-841461416eb2f73a78b40f35**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T19:51:17Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7266 routes; SHA-256 `d391ccf0bfc0382e8d38e6e768c3436fe8bfa0a210c554f84f9eff0de05097dd`
- Route locales: en=2422, es-419=2422, zh-Hans=2422
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3348, search=3, status=3, story=2835, subscribe=12, topic=768, topics=3
- Story routes: 2835 for 945 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `b0435315b919a640a0990184b42db44247eacf69a1386432dbd318c813207e22`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5a76a92d9d6b61efe5962e4830aa809d245aeb27bc3009b9ca0d69311987a186`
- Candidate tree: 26647 files, including 2850 local story-media files; SHA-256 `e7b93627c5295dac0505c3e8be73b2a52b72cf7bef9e18b7b6ea80388449380a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
