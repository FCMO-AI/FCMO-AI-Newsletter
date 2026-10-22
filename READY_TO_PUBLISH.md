# FCMO AI Newsletter — static-paper release receipt

Release: **newswire-d8656fe2e9131d819aaa847c**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `fcmo-paper-receipt-v1`
- Story schema: `fcmo-stories-v2`
- Newsroom-status schema: `fcmo-newsroom-status-v2`
- Story layer generated at: `2026-10-22T12:11:32Z`
- Edition: `2026-10-22` (`DELAYED`)

## Final route/data manifest

- `data/routes.json`: 5175 routes; SHA-256 `f8fb58660b40adeaf8f2ea7b2f0d95c8f6cdd042a92a1c660c7b98ee1e36f9c5`
- Route locales: en=1725, es-419=1725, zh-Hans=1725
- Route kinds: about=3, agenda=3, archive=21, author=3, beat=27, community=3, correction=12, corrections=3, edition=123, feeds=3, front=3, guide=3, landing=3, legal=9, letters=3, method=3, org=2451, search=3, status=3, story=1950, subscribe=15, topic=528
- Story routes: 1950 for 650 live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `36b8b6a06c018fa37499738e1a855941a14d0054240309b587a57c0e1d76fea9`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `ed20b1f0f778f20532d0223a17705a1baa5a730a91b47110366ed297cdd3204d`
- Candidate tree: 18643 files, including 1962 local story-media files; SHA-256 `f7e894a476c0b0710125cb84898830a4fa55bb2a0efe832d6b77e87563686928`

## Verification boundary

This receipt freezes the automated Story/status edition. Human pieces and curated issues are independently committed through review; the combined publication must pass `PIECE_VALID`, all fourteen gates and the browser oracle.

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
