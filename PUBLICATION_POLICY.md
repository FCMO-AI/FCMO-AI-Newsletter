# Publication safety policy

FCMO AI Newsletter is a public-only publication repository.

## Safety boundary

This repository must contain only material intended for public release. It must never contain private research workspaces, internal agent state, internal project-specific relevance, private hypotheses or experiments, operational logs, source-repository history, upstream commit identifiers, personal email addresses, credentials, or private keys.

The generated newsletter is published only after an upstream fail-closed publication pipeline has produced a public release artifact. The public repository does not fetch, clone, or authenticate to private research repositories.

## Safe-fail rule

If publication validation fails for any reason, this repository is not updated. The previous public version remains live.

No failed privacy check may be bypassed merely to refresh the website.

## Repository structure

- `site/` — generated public static site; replaced atomically by approved publication output.
- `.github/workflows/pages.yml` — public GitHub Pages deployment only.
- repository documentation — public operational/documentation material only.

The public repository's git history is independent and must never share ancestry with a private source repository.
