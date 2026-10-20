# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-6614d67abeb6daea68b51f18**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-20T09:14:45Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4854 routes; SHA-256 `894aa585dfc54ba1f40d170304a5808e3e4842d28402a0822cb322f4ce424e10`
- Route locales: en=1618, es-419=1618, zh-Hans=1618
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2307, search=3, status=3, story=1824, subscribe=15, topic=516
- Story routes: 1824 for 608 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `1fc319765958294cd8e131b2605d55caa58eabf322716047572ac300bdc90e42`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `4089143c842aeb53f88b1282eab19bbc399ad3d468a0cddea862fcf522f24f17`
- Candidate tree: 17498 files, including 1833 local story-media files; SHA-256 `5b41515bbfbd96ea4f12d2cf377970d63c571ea47aad5eecfe15bfaebbc693fe`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
