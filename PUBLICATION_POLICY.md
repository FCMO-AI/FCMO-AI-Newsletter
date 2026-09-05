# Publication safety and autonomous-newsroom policy

FCMO AI Newsletter is a **public-only publication repository**. It is the public sink and public newsroom, not the private research workspace.

## Safety boundary

This repository must contain only material intended for public release. It must never contain private research workspaces, internal agent state, internal project-specific relevance, private hypotheses or experiments, operational logs from a private source, private-source repository history, upstream commit identifiers, personal email addresses, credentials, private keys or inherited private strategic implications.

Only a sanitized, semantically declassified, allowlisted public corpus may cross the upstream publication airlock. The public repository does not fetch, clone or authenticate to a private research repository.

The public newsroom may independently reach its own analysis by using the sanitized dossier plus public web evidence. That analysis must have public provenance and may never be produced by smuggling private ARB context into a prompt.

## Operational truth

A valid corpus contains both an upstream `newsroom-release.json` and a downstream `_transport-receipt.json` for the same digest. `tools/airlock_health.py` distinguishes a healthy `NO_PUBLIC_DELTA` heartbeat from `PUBLIC_DELTA` and from actual transport starvation.

Missing or stale input is an operational failure, not a successful green no-op.

## Autonomous newsroom sequence

The daily newsroom cycle is:

1. verify fresh airlock delivery and digest;
2. regenerate canonical public English from `corpus/`;
3. run clean-room public web research for newly ingested dossiers;
4. prune locale fields that the semantic boundary has reclassified private;
5. generate missing ES-419/ZH-Hans translations;
6. run an independent language-editor pass and bind PASS receipts to source/translation digests;
7. build the newspaper Story wire without changing canonical evidence semantics;
8. run the Visual Desk, quarantining image discoveries until reuse rights are proved and generating FCMO-owned art when not;
9. enforce media-rights policy;
10. generate localized stable routes, `NewsArticle` metadata, sitemap and News sitemap;
11. freeze the deterministic overlay, rebuild the public receipt and run all publication gates;
12. commit only public release state;
13. deploy through Pages and verify that the expected release identity is actually live.

## Safe-fail rule

If privacy, semantic declassification, transport integrity/freshness, public research, localization, independent translation review, media rights, release integrity or deployment verification fails, the public release is not advanced. The previous deployed version remains live. No failed gate may be bypassed merely to restore green CI or refresh the website.

## Repository structure

- `corpus/` — sanitized public handoff produced by the upstream publication airlock; never raw private research state;
- `site/` — checked-in public base tree, shared assets, legal pages, curated locale packs, translation-review ledger and clean-room public-research records;
- `release-src/` — editable canonical English release source regenerated from the sanitized corpus, including Story/distribution surfaces after an autonomous refresh;
- `release-overlay/final/` — deterministic frozen package of `release-src/`, hash-checked before assembly;
- `newsroom-work/` — ephemeral quarantine/workspace for discovered assets that have not earned publication rights; never committed by the refresh workflow;
- `tools/` — ingest, research, localization, story, visual, distribution, release, receipt and verification tooling;
- `publish/` — ephemeral assembled deployment candidate, never the authority-bearing source;
- `.github/workflows/daily-refresh.yml` — fail-closed airlock → ingest → research → translation/review → Story/visual/distribution → validation → commit cycle;
- `.github/workflows/pages.yml` — assembles and deploys only a validated public candidate and, after Airlock-v2 activation, runs a post-deploy live oracle.

The public repository's git history remains independent from every private source repository.
