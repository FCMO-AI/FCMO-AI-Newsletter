# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-46730678ce22118afa986fef**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T06:57:22Z`
- Edition: `2026-11-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7134 routes; SHA-256 `280eb36d8d1316e8ed0979ef6e0177b24c9f2e99d05dcc0088f4db5aa9d662d2`
- Route locales: en=2378, es-419=2378, zh-Hans=2378
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3294, search=3, status=3, story=2778, subscribe=12, topic=753, topics=3
- Story routes: 2778 for 926 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `05d82e0ecd1fe2d47e54c222099889e3be345bf583ab5c3f1ee7c98eeb98eea7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d324164df8963e3a4815f0ff7dd9057a9f39b6f41fbe37b765c18e44a84c4104`
- Candidate tree: 26136 files, including 2793 local story-media files; SHA-256 `fc4c921be3f440ffb05be6a69bb2e3d23c759c46cb8a48cb68e7816e377f5798`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
