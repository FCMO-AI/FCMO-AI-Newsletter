# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-aa57f37e6b5a36af3f1b48ef**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-21T00:19:13Z`
- Edition: `2026-10-20` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 4929 routes; SHA-256 `71d1e7fc18db6f4496c90799274fb16c2584002977b59f081717c75c0a897836`
- Route locales: en=1643, es-419=1643, zh-Hans=1643
- Route kinds: about=3, agenda=3, archive=3, author=3, beat=15, community=3, correction=9, corrections=3, edition=117, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2337, search=3, status=3, story=1863, subscribe=15, topic=522
- Story routes: 1863 for 621 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `a78db09bfe6b391705d1e17aaa90d56d49360ec4538422cbfa2234a0e6eb0dca`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `51233ef51da2a8769d7e73aeeedcf8aee019d1a974b00a93543a818248b345ea`
- Candidate tree: 17826 files, including 1872 local story-media files; SHA-256 `fc73973bce1f1e9d19c0fc92c0246147bea32af9ab91f6f9cfd69631619b64d8`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
