# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-459e84ab07b9a500798648ff**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T17:26:29Z`
- Edition: `2026-10-21` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 5073 routes; SHA-256 `0971ef91089ed805e2b48588e76513ec2ed00419dad682f5af9941e9821a4eec`
- Route locales: en=1691, es-419=1691, zh-Hans=1691
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=120, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2394, search=3, status=3, story=1911, subscribe=15, topic=525
- Story routes: 1911 for 637 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `2cf25d8c2dd2e38f098cc03a19f3f4b80ac59effb64b8414eca6f0921d5e6ac9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8f3407f0451f3cfb24c5eb0457bffd612f33465a69986f7e1db8e9fd4e309b4b`
- Candidate tree: 18285 files, including 1923 local story-media files; SHA-256 `5a6cc035fbd6bb48df27e9add80cf3c70db8baae89142612c03b53e681551600`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
