# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a9cfde04cc3eb198bcbcd700**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-14T23:08:32Z`
- Edition: `2026-10-14` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 3696 routes; SHA-256 `b3839a85b1133070bc9a4426f999e3a8b4f1a926b9567b718923bb56dc79106f`
- Route locales: en=1232, es-419=1232, zh-Hans=1232
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=99, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=1791, search=3, status=3, story=1341, subscribe=15, topic=375
- Story routes: 1341 for 447 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `c7df0f6b47c7a725253d956922fc57b2597dbee8687d567f53866d9b0f185a4a`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `dff71eed65ba79ef3cbf8745be91398af09e22b651ecf79ee3b26040bb62d077`
- Candidate tree: 13240 files, including 1350 local story-media files; SHA-256 `0971ee4239715181b49ed8357a057d841dac73b78c7bba971e9aca9ad473cdf3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
