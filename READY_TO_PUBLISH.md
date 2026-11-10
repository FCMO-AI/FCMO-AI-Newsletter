# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-df550885cd2841c1dfe6369b**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T10:02:33Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7209 routes; SHA-256 `d19c4f6f7b61f2bb62a19f241ac00cae49c498bc5cfd5a0fe43561a0b34703a1`
- Route locales: en=2403, es-419=2403, zh-Hans=2403
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3324, search=3, status=3, story=2811, subscribe=12, topic=759, topics=3
- Story routes: 2811 for 937 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `ff9d23b3877bdbc598806beee3d9cc1d0a4b204e3260b1c26e6aaa2b7f9e0b28`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `035b45130df899dee2734fc7b3d3b40e63e1b4d4ba5f383a5afb3bce01999eb0`
- Candidate tree: 26439 files, including 2826 local story-media files; SHA-256 `f54f593638ac08fa717a0755f0b6bc7b56e8c334316a01135a6348f0ff693a05`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
