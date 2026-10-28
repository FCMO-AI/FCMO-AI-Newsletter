# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d99eda908afc2713b7bae1e3**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-28T09:06:07Z`
- Edition: `2026-10-28` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 5919 routes; SHA-256 `2216acedda03efca4477fea19d475878dffd06944d0b65da90dc54d813a3e5f3`
- Route locales: en=1973, es-419=1973, zh-Hans=1973
- Route kinds: about=3, agenda=3, archive=24, author=3, beat=33, correction=15, corrections=3, edition=141, feeds=3, landing=3, legal=9, method=3, org=2778, search=3, status=3, story=2259, subscribe=12, topic=621
- Story routes: 2259 for 753 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1e68048f315436afd2d8848f072f7f3961e6b5ef34cc55d26402ec163e86e6d7`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `5cb35833e7453adaebfb24e8580c0cf9fc1a91d40c4619fe254b3697cc818bee`
- Candidate tree: 21455 files, including 2274 local story-media files; SHA-256 `05f51d54541d02a2de02d8796f8db634f150af9cb07bb24a59144ed48f58bc07`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
