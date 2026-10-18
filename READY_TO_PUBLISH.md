# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-daa9fc36dec4a86380ee6ced**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-18T10:11:01Z`
- Edition: `2026-10-18` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4629 routes; SHA-256 `8ffb868820936f187be771038ab664fb3c444e7608556d4a89905756ff51b406`
- Route locales: en=1543, es-419=1543, zh-Hans=1543
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=111, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2208, search=3, status=3, story=1722, subscribe=15, topic=498
- Story routes: 1722 for 574 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `2028f706b91db504ee86ba3dd8c01004b45bd7b8d2b012109b9ce456ba7f0b48`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `676c7a4576407774f99c0ca4349b18b841231c4e3b51f90407c2cd4fba4ba133`
- Candidate tree: 16632 files, including 1731 local story-media files; SHA-256 `657a40692007823ae37cbc04dc61bb1583f4d1e0a0e6547e2adfdf5579f3aac3`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
