# Publication safety policy

FCMO AI Newsletter is a public-only publication repository.

## Safety boundary

This repository must contain only material intended for public release. It must never contain private research workspaces, internal agent state, internal project-specific relevance, private hypotheses or experiments, operational logs, source-repository history, upstream commit identifiers, personal email addresses, credentials, or private keys.

The generated newsletter is published only after an upstream fail-closed publication pipeline has produced a public release artifact. The public repository does not fetch, clone, or authenticate to private research repositories.

## Safe-fail rule

If publication validation fails for any reason, this repository is not updated. The previous public version remains live.

No failed privacy check may be bypassed merely to refresh the website.

## Native-language publication rule

The Newsletter has exactly three native publication languages: canonical English (`en`) plus curated Latin American Spanish (`es-419`) and Simplified Chinese (`zh-Hans`). External/browser translation is outside this contract.

Every public development must carry committed Spanish and Simplified-Chinese translations of its `title`, `summary`, and `why_it_matters`. The public Pages build validates this against the complete set of development IDs and fails closed if either locale or any required field is missing. Runtime machine translation and silent generative fallback are forbidden.

Curated translations are source-controlled publication material. They must preserve claim strength, uncertainty, numbers, technical identities, evidence/confidence distinctions, and material caveats. They are not represented as human reviewed unless that review actually occurred. See `I18N.md` for the complete localization contract.

## Repository structure

- `site/` — generated public static site; replaced atomically by approved publication output.
- `site/data/translations.json` — reviewable curated story translations for the two non-canonical native locales.
- `tools/i18n_site.py` — deterministic localization validation and presentation layer; contains no translation provider.
- `.github/workflows/pages.yml` — public GitHub Pages deployment only.
- repository documentation — public operational/documentation material only.

The public repository's git history is independent and must never share ancestry with a private source repository.
