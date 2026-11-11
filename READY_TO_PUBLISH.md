# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-eaad87226e88c3c841153e73**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-11T09:35:22Z`
- Edition: `2026-11-11` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7317 routes; SHA-256 `37eca27e20b4bf87a8a1b91934824e8aa5b61e0c293ecffc4dc71b0d67a49d7d`
- Route locales: en=2439, es-419=2439, zh-Hans=2439
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=39, correction=15, corrections=3, edition=183, feeds=3, landing=3, legal=9, letters=3, method=3, org=3357, search=3, status=3, story=2865, subscribe=12, topic=774, topics=3
- Story routes: 2865 for 955 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `851402c72f4da1847cef844f292943856b8baff7585776fd4c4c615159e3584c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ca39b85182adf23442b05a3a03f16aaa2f352f35bc2ce29d76f9dece796c4dd9`
- Candidate tree: 26886 files, including 2880 local story-media files; SHA-256 `dd7820f2924d462362c7fcb201f8738597e5312f85ef2935ec903a530dacaf8a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
