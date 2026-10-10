# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eea6e0cceb493828ebd27d65**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-10T03:19:42Z`
- Edition: `2026-10-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 1959 routes; SHA-256 `d2c9acf69528ae0bde98227faecd3710d7353cb06a95cbfb9f6c8b78ab6977f2`
- Route locales: en=653, es-419=653, zh-Hans=653
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=84, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=981, search=3, status=3, story=621, subscribe=3, topic=195
- Story routes: 621 for 207 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `fac0ccc8c4dc511ef7115901eab9367d2e86b13fc332eac6110ed3b37e31059e`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `215ddff13b1e0d2f099a0df5dce783005333949400f11f8f07dbabde3fa19b76`
- Candidate tree: 6835 files, including 630 local story-media files; SHA-256 `d8779f0a7040b2586bd8b7755e72bf9adb2825ca9384ad4a064b875f9c192ec4`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
