# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-053cfd9ab8b97d11746c7281**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-18T15:02:20Z`
- Edition: `2026-11-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7503 routes; SHA-256 `f44a6af774ec6dd62cb7e5372ec79d36623368476c29f136d8ce48c1bf9fb160`
- Route locales: en=2501, es-419=2501, zh-Hans=2501
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=195, feeds=3, landing=3, legal=9, letters=3, method=3, org=3420, search=3, status=3, story=2955, subscribe=12, topic=795, topics=3
- Story routes: 2955 for 985 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `4cb4d3cbcc5ce4fd842dc7d1dc28aa3935f7f42906df2903b323a5561094e072`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8dae2ab0cdd641784207794e6dd3abbdd3e3153c5f0e0e7f13c842da937d0f0f`
- Candidate tree: 27686 files, including 2970 local story-media files; SHA-256 `7c9609c06e441f50d9f9731e9cab94cb4bf8552f41a1d12a1aef26ecf2be411b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
