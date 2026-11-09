# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-a72c12ee122c76c82a908ec5**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-11-09T19:47:08Z`
- Edition: `2026-11-09` (`FRESH`)

## Final route/data manifest

- `data/routes.json`: 7161 routes; SHA-256 `b4a0a7ae0943257ed84762de6c32c1df40bba0046eaf42e3d0a53feeefc0ee0a`
- Route locales: en=2387, es-419=2387, zh-Hans=2387
- Route kinds: about=3, agenda=3, archive=30, author=3, beat=36, correction=15, corrections=3, edition=177, feeds=3, landing=3, legal=9, letters=3, method=3, org=3303, search=3, status=3, story=2790, subscribe=12, topic=756, topics=3
- Story routes: 2790 for 930 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `712fb04dfa0a9bf38febd500d46025cf15fa1bc97429767188e1595ba1bc3607`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `302ddc12c17dc38f15c8eb7f3377605424a0b62ddcd61c3514f6ae90b34ce3aa`
- Candidate tree: 26247 files, including 2805 local story-media files; SHA-256 `c3fbbd668ee6f45e2c6ba800ac2811bd59bc5830a49a100f51c13277cc910af9`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
