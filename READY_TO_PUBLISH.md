# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-95dda34d0f6d190afa108f8c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-13T19:59:23Z`
- Edition: `2026-10-13` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3174 routes; SHA-256 `3ec924ef1d10169f95c3aafa3f21dc65cb3c2f5cae02748bb37047bf99f7c1e7`
- Route locales: en=1058, es-419=1058, zh-Hans=1058
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=96, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1548, search=3, status=3, story=1113, subscribe=15, topic=327
- Story routes: 1113 for 371 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `dc60229a30e9c5bcd73081aad5a9d7c902688dd0827849600b69ebbe6150f918`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e7651c89deb8da65ed19937b37fe1acf73a6f9a9f5dec87ac006fee455efc71f`
- Candidate tree: 11268 files, including 1122 local story-media files; SHA-256 `a20a399cc0549bc20eeac7084f997a778d5f6c868adb248ba68cc0a74c1e9a3a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
