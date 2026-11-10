# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-9b64a8db86eb5928d74369e6**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-10T17:39:31Z`
- Edition: `2026-11-10` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7251 routes; SHA-256 `c356431c0b52d355f7689d58ef0563012e24e084ae921746285d8e5ab20b0894`
- Route locales: en=2417, es-419=2417, zh-Hans=2417
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=180, feeds=3, landing=3, legal=9, letters=3, method=3, org=3342, search=3, status=3, story=2829, subscribe=12, topic=765, topics=3
- Story routes: 2829 for 943 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `d87f63318d1010197292c4bfe4984f0d151bad0d4831bd508d34be5003a02ba2`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `cf7bfe709e05ad3ede7bcfdd285aff5e5aa0f57bc72c1a547597d97bb8c097ff`
- Candidate tree: 26597 files, including 2844 local story-media files; SHA-256 `459705436561d9f0c42fcd7c275343d881d5cec654e8c2b72c592e93dac97f6b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
