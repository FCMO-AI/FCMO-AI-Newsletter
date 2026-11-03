# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-3164203e5a9a563344ca25c5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-03T10:32:31Z`
- Edition: `2026-11-03` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 6720 routes; SHA-256 `cfbc0f333c40004bc42270576cabdd65fb9c32c351cf83a280d6aa3d0950b669`
- Route locales: en=2240, es-419=2240, zh-Hans=2240
- Route kinds: about=3, agenda=3, archive=27, author=3, beat=36, correction=15, corrections=3, edition=159, feeds=3, landing=3, legal=9, letters=3, method=3, org=3132, search=3, status=3, story=2598, subscribe=12, topic=702
- Story routes: 2598 for 866 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `24d39e235ed779c6a3d88b5e7cc051917ae18d21cdf916ca83402faf6daf8c54`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ed53030e68bb5e870b7fcbe6d23100ee37d63d489b92b36cbf52a8e8777b34f5`
- Candidate tree: 24526 files, including 2613 local story-media files; SHA-256 `db9008dc02b2c28aaf0e1eaa94fe43bdf3351fb16bf19ab548ce19d4d17f078f`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
