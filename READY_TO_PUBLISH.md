# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-08a149ab8fd913a11df4463f**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T02:34:31Z`
- Edition: `2026-11-08` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7134 routes; SHA-256 `d37cce6e261cd392322a37d314bc4ca3e105ea0379337517b8d9b2138028a673`
- Route locales: en=2378, es-419=2378, zh-Hans=2378
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=174, feeds=3, landing=3, legal=9, letters=3, method=3, org=3294, search=3, status=3, story=2778, subscribe=12, topic=753, topics=3
- Story routes: 2778 for 926 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `0f24e9a69aa931473dbf15a534b872b252a66f0b076426d8648dd0779186fd9c`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `a73a11da46abc2f16b1ce79594ee4909db2e8875bd29ea51d1cc71d7a20fc940`
- Candidate tree: 26134 files, including 2793 local story-media files; SHA-256 `8b86d452264731e37eccb16a26d3e269b2cdecb32851aca4e19eac3b2b18bf35`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
