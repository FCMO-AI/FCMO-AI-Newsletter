# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-901a8c9f464cc92b70e0fd5b**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-23T14:13:10Z`
- Edition: `2026-10-23` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5316 routes; SHA-256 `a00a0277fee99a83d47684730d72b23e9dc92da5a11cbe489a1f093bfda8a57b`
- Route locales: en=1772, es-419=1772, zh-Hans=1772
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=126, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2526, search=3, status=3, story=2004, subscribe=15, topic=537
- Story routes: 2004 for 668 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `4bf7d79696bc1a5666d2b57d1560755dc1c656a29141d8533eaea3b7348ed9b7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `c272469e2734dd000df275c9ef3e20ebd5ee6b7eb705c6b54e04f4aab2040947`
- Candidate tree: 19156 files, including 2016 local story-media files; SHA-256 `278fef20bfa10242c5ddbfaadf01d727c439fba7c7773a52f936a139ea35814e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
