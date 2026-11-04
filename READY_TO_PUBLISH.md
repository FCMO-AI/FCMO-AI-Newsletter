# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a6dbd4751077c30938f90e82**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-04T02:10:13Z`
- Edition: `2026-11-03` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6798 routes; SHA-256 `7597adaded9b04c16fb52a228180d7d5a803efdabea5fe7b245008a75a707bd7`
- Route locales: en=2266, es-419=2266, zh-Hans=2266
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=159, feeds=3, landing=3, legal=9, letters=3, method=3, org=3177, search=3, status=3, story=2628, subscribe=12, topic=705
- Story routes: 2628 for 876 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1645affeba87f5665803814826296dd0a402605eb3b8f6cf7802bb04d7c35774`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `e0962d94a6ace5cd45ad32d06eff2b7029f621b1e0cffe267878113e2b0fa598`
- Candidate tree: 24805 files, including 2643 local story-media files; SHA-256 `33c5ded3079d786717c356aacb9930eb206a22136a454acbc9b023133ddafc0b`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
