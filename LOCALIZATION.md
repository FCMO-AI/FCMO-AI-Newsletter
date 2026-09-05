# FCMO AI Newsletter native-edition contract

English is the **canonical semantic source**. FCMO AI Newsletter supports exactly three native editorial locales:

- `en` — English, canonical semantic source;
- `es-419` — Latin American Spanish;
- `zh-Hans` — Simplified Chinese.

Browser extensions, operating-system translation and third-party translation layers are outside this contract.

## Editorial ownership

The ARB research/publication agent that prepares a publishable development owns the complete three-language publication obligation. The same editorial task produces the English public wording plus its Spanish and Simplified Chinese editions **before the material crosses the airlock**.

Newsletter does not call a translation model, translation API or language-review provider. GitHub Actions does not generate prose. The public repository is a deterministic sink: it imports the already-airlocked locale deltas, validates them, builds static routes and publishes them.

This keeps the agent that actually understands the source evidence responsible for carrying intent, caveats, evidence strength and terminology across languages instead of asking a second model to reconstruct that context later.

## What “native editorial edition” means

Translate intent rather than English syntax while preserving:

- evidence strength and uncertainty;
- demonstrated vs. claimed vs. inferred distinctions;
- caveats and contradictory evidence;
- numbers, versions, benchmark names and model identities;
- stable FCMO IDs and URLs;
- the scope and regime in which a result is true.

Spanish and Chinese are source-controlled publication artifacts. They are not labelled human-reviewed unless a qualified human actually reviews them.

## Coverage contract

Every canonical public record must have Spanish and Chinese coverage for every reader-facing prose field that survives declassification, including title, summary, why-it-matters, importance rationale, limitations, contrary evidence, claim text, evidence-gap descriptions, relationship summaries and public technical prose.

Coverage is dynamic. If English contains `N` stable public story identities, both native non-English editions must contain the same `N` identities. A new story without both editions is a release failure, not permission to publish English-only.

Private strategic implication fields are outside the public language obligation because they do not cross the airlock.

## Airlock transport

ARB may emit locale deltas at:

- `data/locales/es-419/records.json`
- `data/locales/zh-Hans/records.json`

inside the sanitized public release. `tools/sync_airlocked_locales.py` merges those deltas into Newsletter's committed locale packs. Existing historical translations remain stable when a release contains no locale delta.

`tools/reconcile_locale_overlays.py` then prunes fields that no longer exist in the declassified public schema, so an old translated field cannot resurrect material that the airlock removed.

## Deterministic integrity gate

`tools/validate_localizations.py` is deliberately **not a translator and not a semantic-language model judge**. It proves high-value invariants that software can prove honestly:

- exact story-ID parity across English, Spanish and Chinese;
- overlay shape compatible with the current declassified English record;
- required title/summary/why-it-matters coverage;
- exact preservation of numeric tokens, stable FCMO IDs and embedded URLs;
- basic Simplified-Chinese script sanity for substantial prose;
- rejection of an edition that is simply unchanged canonical English;
- deterministic source and locale digests recorded in `site/data/i18n/integrity-manifest.json`.

The receipt explicitly records `editorial_owner: "ARB publication agent"`, `human_reviewed: false` and `network_translation: false`.

A deterministic checker cannot prove literary quality. Editorial equivalence remains the publication agent's responsibility and is reviewable through source control and the public evidence record.

## Runtime behavior

The app-shell locale resolution remains deterministic:

1. explicit `?lang=` parameter;
2. saved manual selection;
3. browser language preference;
4. English fallback.

All `es-*` browser locales resolve to `es-419`; all `zh-*` locales resolve to `zh-Hans`.

Runtime behavior is presentation lookup only. There is no generative fallback and no remote translation endpoint. Missing locale material is a build defect.

## Static newspaper routes

The Story layer emits crawlable static routes:

- `/news/en/...` for English;
- `/news/es/...` for `es-419`, exposed with `hreflang="es"`;
- `/news/zh-hans/...` for `zh-Hans`, exposed with `hreflang="zh-Hans"`.

Each story has reciprocal language alternates plus `x-default`. `/news/` is a native-edition gateway, not a translation service.

## Source-control layout

- `site/data/i18n/es-419/part-*.json` + `ui.json` — Spanish editorial records and UI catalogue;
- `site/data/i18n/zh-Hans/part-*.json` + `ui.json` — Simplified-Chinese editorial records and UI catalogue;
- `site/data/i18n/integrity-manifest.json` — deterministic three-language integrity receipt;
- `site/assets/curated-i18n.js` / `.css` — deterministic presentation layer;
- `tools/sync_airlocked_locales.py` — import of ARB-authored locale deltas;
- `tools/reconcile_locale_overlays.py` — public-schema reconciliation;
- `tools/validate_localizations.py` — provider-free publication gate;
- `tools/apply_curated_i18n.py` — coverage validation and bundle injection.

## Publication gate

A release fails if:

- either non-English edition omits a canonical FCMO ID or contains a stale/extra ID;
- reader-facing required prose is absent or empty;
- translated structure no longer matches the declassified public structure;
- numbers, FCMO IDs or embedded URLs drift;
- a substantial Chinese edition lacks expected Han-script content;
- a purported non-English edition is unchanged canonical English;
- public brief/stable-route identities disagree with canonical English;
- a runtime translation endpoint or external model credential is introduced;
- any native editorial locale outside `en`, `es-419`, `zh-Hans` is exposed;
- the localized build cannot be traced to the frozen canonical English identity.

A new or materially changed story and its two additional native editions are **one publication obligation**. The system fails closed rather than manufacturing a downstream translation or publishing a partial edition.
