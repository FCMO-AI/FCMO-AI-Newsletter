# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-60056c28ba947c25dd1ea27c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T19:46:01Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5976 routes; SHA-256 `9fc077b5b5600ac0b016e46356886289fe359d72d560cccff7167611f046cc75`
- Route locales: en=1992, es-419=1992, zh-Hans=1992
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2799, search=3, status=3, story=2289, subscribe=12, topic=627
- Story routes: 2289 for 763 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `784ccba43ffaf28c06dd30b2729c6f8087253df4b9bb1ea9a3bc026a6e032ef9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `8ee83760c7ad5a4f3872a5e78447808dad572f20d5464875e4edb8e9b69dc556`
- Candidate tree: 21699 files, including 2304 local story-media files; SHA-256 `d827b322adf74d27a84f1241649dfe41a9f3534eb7688072432736f724ab0f7a`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
