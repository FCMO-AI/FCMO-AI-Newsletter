# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c82258f927d94f0d4cec3bab**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T12:00:33Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3027 routes; SHA-256 `86668903cb6db64c1fa1ab3fbb5daf0165f88b7fb00063fcacf72e7e531dac01`
- Route locales: en=1009, es-419=1009, zh-Hans=1009
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1488, search=3, status=3, story=1044, subscribe=15, topic=309
- Story routes: 1044 for 348 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c0e6923bfccebf51d015b723c7e1d4bd0679b15686ca80a54d39fe4cfb3ef035`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `106e6567dc6ede32798e5bedf404a4cc6e2e7541c02f9071958c9497d68f70d7`
- Candidate tree: 10695 files, including 1053 local story-media files; SHA-256 `910c3bf63f79a44d7b4afd5619ec98e0c87364f2f9bd0fd389a00affdd22e551`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
