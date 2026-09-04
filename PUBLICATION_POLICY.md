# Publication safety policy

FCMO AI Newsletter is a **public-only publication repository**. It is the public sink, not the private research workspace.

## Safety boundary

This repository must contain only material intended for public release. It must never contain private research workspaces, internal agent state, internal project-specific relevance, private hypotheses or experiments, operational logs from a private source, private-source repository history, upstream commit identifiers, personal email addresses, credentials or private keys.

Only a sanitized, allowlisted public corpus may cross the upstream publication airlock. The public repository does not fetch, clone or authenticate to a private research repository.

## Safe-fail rule

If privacy, integrity, localization or release validation fails, the public release is not advanced. The previous deployed version remains live. No failed privacy check may be bypassed merely to refresh the website.

## Repository structure

- `corpus/` — sanitized public handoff produced by the upstream publication airlock; never raw private research state;
- `site/` — checked-in public base tree, shared assets, legal pages and curated locale packs;
- `release-src/` — editable canonical English release source regenerated from the sanitized corpus;
- `release-overlay/final/` — deterministic frozen package of `release-src/`, hash-checked before assembly;
- `tools/` — ingest, localization, release, receipt and verification tooling;
- `publish/` — ephemeral assembled deployment candidate, never the authority-bearing source;
- `.github/workflows/daily-refresh.yml` — fail-closed corpus → translation → overlay → receipt → validation → commit cycle;
- `.github/workflows/pages.yml` — assembles and deploys only a validated public candidate.

The public repository's git history remains independent from any private source repository.
