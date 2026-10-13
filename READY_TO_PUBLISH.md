# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-166270dfbee20d2be7ae878f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T17:01:26Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3132 routes; SHA-256 `b31c8759b7558268124a659da0a2b5f08205ace78be7f458f1a1d4fe54a81f42`
- Route locales: en=1044, es-419=1044, zh-Hans=1044
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1533, search=3, status=3, story=1089, subscribe=15, topic=324
- Story routes: 1089 for 363 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `020cf11151fc8fbc57fc6e89b5adb774e40311fb6850b5ae4f7311b50877c7c6`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `7ff2aec4cef86c2e270ab329b26796b4c8ecea3ad51527b0573da8754c7b1ce9`
- Candidate tree: 11077 files, including 1098 local story-media files; SHA-256 `98603ab3fe58670bc24985a2e679529b6f89bde4dab7f9d7715ab8a1ac34189e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
