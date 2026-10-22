# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-db097dd1b2db3d4e16cf84a0**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T03:13:59Z`
- Edition: `2026-10-21` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5094 routes; SHA-256 `8441d5d593494a68c1a457db78ed17907aad25993f421aebfcb1eead41bd3894`
- Route locales: en=1698, es-419=1698, zh-Hans=1698
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2406, search=3, status=3, story=1920, subscribe=15, topic=525
- Story routes: 1920 for 640 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fa0b0217d2b29b56af0bb8621738c7bac9294d526c9f6f2f72fcbcc2282dbe93`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `159022ed9bafc4d18f016aad85bceb73b0d5175c8ebb75474661e11d2db9dc6a`
- Candidate tree: 18366 files, including 1932 local story-media files; SHA-256 `01ca63a57eabca75b9f7fae0dbe33677a2cd4916da313e6e50342f556cec52f6`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
