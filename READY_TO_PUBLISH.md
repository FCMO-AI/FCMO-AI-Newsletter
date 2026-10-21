# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-459e84ab07b9a500798648ff**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T15:44:35Z`
- Edition: `2026-10-21` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 5073 routes; SHA-256 `aa28f46c34487bf18fc10284bfdce5c5c6e47137dd86abe482fa1265f5599637`
- Route locales: en=1691, es-419=1691, zh-Hans=1691
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2394, search=3, status=3, story=1911, subscribe=15, topic=525
- Story routes: 1911 for 637 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0e01b14f5d43d2934edce28bd1fa04763696e9365d90debfb23547c8397271bd`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `417475ec7771f5e93594d933488b2db3a3db96f82666062097e55b367d881246`
- Candidate tree: 18287 files, including 1923 local story-media files; SHA-256 `475340baad7f4e87be9bf97cebbe555578c17ea45237033c39adca0ef317e35d`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
