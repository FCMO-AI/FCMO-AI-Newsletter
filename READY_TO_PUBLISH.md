# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-38864ff1aabcb62330d12c86**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-06T14:38:41Z`
- Edition: `2026-11-06` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7038 routes; SHA-256 `88b76c81c81ec6404c92da89afdf32fb041c2bf2052a44fdb96270c7dbaa7e1e`
- Route locales: en=2346, es-419=2346, zh-Hans=2346
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=168, feeds=3, landing=3, legal=9, letters=3, method=3, org=3267, search=3, status=3, story=2730, subscribe=12, topic=741
- Story routes: 2730 for 910 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `de3ca84185a9bafa28db9cc90841e61f9639307898dec544a8a11317744b9ddf`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `d2e4fa2f4815bc7b7e1adc755f898d5a46835fd25dabfced9a89386a8ae944ae`
- Candidate tree: 25724 files, including 2745 local story-media files; SHA-256 `b43de6fbeddf9f4b6b80f614d9939ef65025c6488530c6e19d825f928742e2f2`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
