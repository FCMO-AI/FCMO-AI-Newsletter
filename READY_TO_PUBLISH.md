# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-c253da3ada978a4c28083972**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-07T22:42:08Z`
- Edition: `2026-10-07` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 618 routes; SHA-256 `05ecdbe2b1ea3c1b9dbf3ecad3eafac3a1b70728eb7979e57ae4f5c249138c76`
- Route locales: en=206, es-419=206, zh-Hans=206
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=78, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=267, search=3, status=3, story=150, subscribe=3, topic=45
- Story routes: 150 for 50 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `48bdb4f817b458cdbd0c0eeb0c527fb6f21667923e4946c550c318e38b91c243`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `34949fd91d923d179d1230177cea1d87adbd2dcf36bf0aea00e79d3bd9edd1b4`
- Candidate tree: 2232 files, including 159 local story-media files; SHA-256 `09ba0b09fd6d5570fff061809341c31ebbe36f1f888f2a965ff09586de4af564`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
