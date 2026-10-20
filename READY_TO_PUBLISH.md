# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f94b3cf79ddbbca8b6adb862**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T11:07:53Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4875 routes; SHA-256 `c817f0901357115fe64d3821d91aec98e1764ff5a1fef30f2f24460f971cd35b`
- Route locales: en=1625, es-419=1625, zh-Hans=1625
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2313, search=3, status=3, story=1833, subscribe=15, topic=522
- Story routes: 1833 for 611 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `69ce0285cf74689af73510581b24b9bd9f261c913715470b9255f7efb2c7251c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `b4ae356e61155393691fff99190d46eee644af6860d57ec658d4a7867607b5f0`
- Candidate tree: 17573 files, including 1842 local story-media files; SHA-256 `24abdff665f4e8947c8a9da68fa07b4eb4bb89c1aec694083005a23aa625fffc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
