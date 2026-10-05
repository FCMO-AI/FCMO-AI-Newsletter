# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d6821759b3a51919c47a5db4**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-05T07:57:48Z`
- Edition: `2026-10-05` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 531 routes; SHA-256 `97f92d3afa6149645d614bd9698a0e4a839ebfd9d4f969ef5f7084f6000447cd`
- Route locales: en=177, es-419=177, zh-Hans=177
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=69, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=213, search=3, status=3, story=129, subscribe=3, topic=42
- Story routes: 129 for 43 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d654f5b30cf585022a5df37ea558b0a45f8a659ff65b911e06430d1aea0ec10a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `72aff2da850f5cb5be57359470d55725d2142f7c0357f70905069437c926a3ac`
- Candidate tree: 1963 files, including 135 local story-media files; SHA-256 `dd823653fc655375d66ef141442f1bd8039a3ab2ba92ede7ed9f609a64bbe546`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
