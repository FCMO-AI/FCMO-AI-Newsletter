# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-69fbb25aa9b2c3253957a344**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T02:36:04Z`
- Edition: `2026-11-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7185 routes; SHA-256 `59e9653d2a94c6baf3f85d609552517a698c830ea34b3d3d0f226cfe5c03e71a`
- Route locales: en=2395, es-419=2395, zh-Hans=2395
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=177, feeds=3, landing=3, legal=9, letters=3, method=3, org=3315, search=3, status=3, story=2802, subscribe=12, topic=756, topics=3
- Story routes: 2802 for 934 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ea62b6623171e566cadfcc6ff448f0b1f0a25395ff7aaf68edc048c849d250ce`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `289825ce436fa2fc15d06d529740ef1521c9109974361f93a69a1ac663d4c5d5`
- Candidate tree: 26350 files, including 2817 local story-media files; SHA-256 `7f537fefe1010a48db4303f0c98401d2034ba57bb6af1313c383e8cf8520dadc`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
