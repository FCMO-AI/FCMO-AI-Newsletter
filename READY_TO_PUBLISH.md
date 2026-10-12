# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-f1bbdaa1020f645431547e60**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T01:59:26Z`
- Edition: `2026-10-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2466 routes; SHA-256 `f6000dd30d7b1ea63aa4437525c7d341e77c6db83dc6d1ee808403af7d0c9e6e`
- Route locales: en=822, es-419=822, zh-Hans=822
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=90, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1236, search=3, status=3, story=813, subscribe=15, topic=237
- Story routes: 813 for 271 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `bd5a1eae0c9a2ee48e5d039e2c6880a9e10e9e40391e2abc53ecae9925b2cabf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e1054195da874b22c9a76b13caa05f22e3c318f8df0677e8750cb5eb2c33c7b4`
- Candidate tree: 8638 files, including 822 local story-media files; SHA-256 `954042fcf851143ba37574c23e22c49df8bfc2b4c252bd0ec9972dfd4d836904`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
