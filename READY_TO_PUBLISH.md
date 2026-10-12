# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-8af765c96ce94f841cd8e3b7**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-12T15:00:13Z`
- Edition: `2026-10-12` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 2787 routes; SHA-256 `1842f8575e9bf2fedf684322101ed558b61526bb2e2f245197faefa10d6cbc09`
- Route locales: en=929, es-419=929, zh-Hans=929
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=93, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1383, search=3, status=3, story=945, subscribe=15, topic=276
- Story routes: 945 for 315 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `df7d289c29de399ad336052121673c15967b7636f895441263971a7bd99388e4`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `edbd6a0f793e9ff3047f4223283b8d62fbaec8269aafa4433fe0e53499d20cbc`
- Candidate tree: 9794 files, including 954 local story-media files; SHA-256 `a1ea7561ea912eb4b9a51a76fdc6c196597c5171cb78938a954968cc330dba3e`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
