# FCMO AI Newsletter native-edition contract

English is the **canonical semantic source**. FCMO AI Newsletter supports exactly three native editorial locales:

- `en` — English, canonical semantic source;
- `es-419` — Latin American Spanish;
- `zh-Hans` — Simplified Chinese.

Browser extensions, operating-system translation and third-party translation layers are outside this contract.

## Editorial ownership

The **FCMO Publication Desk** owns the Spanish and Simplified Chinese editions. It is a scheduled editorial task that works in this repository and nowhere else. It translates from the airlocked English public record only, never from private evidence. It carries intent, caveats, evidence strength and terminology across languages. It writes its translated fields only to `site/data/i18n/<locale>/part-desk.json`, and it appends one line per activation to `ops-ledger:ops/publication-desk/LEDGER.jsonl` in a separate checkout. The product branch does not track the active ledger. Complete the migration in `docs/PUBLISHING-SETUP.md` before resuming ledger writes; missing migration is an operational blocker, not an empty history. ARB's research tasks never translate: ARB's website separation law keeps them out of presentation work. If ARB ever emits locale deltas (see "Airlock transport"), they are still imported.

Newsletter's build does not call a translation model, translation API or language-review provider. GitHub Actions does not generate prose. The public repository is a deterministic sink: it validates the committed editions, builds static routes and publishes them.

Before committing, the desk runs `python3 tools/validate_localizations.py --strict --corpus corpus` and commits only what passes. A pair that is `PENDING` or `FAILED` is shown to readers as an explicit pending page, never as silent English.

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

inside the sanitized public release. `tools/sync_airlocked_locales.py` merges those deltas into Newsletter's committed ARB locale packs. It never reads or writes `part-desk.json`. Existing historical translations remain stable when a release contains no locale delta.

## Provenance and precedence

Each desk record has translated fields under `records.<id>` and matching metadata under `provenance.<id>` in `part-desk.json`: `origin: "publication-desk"`, UTC `at`, `model` when known, `human_reviewed: false`, and `network_translation: false`. The Publication Desk may add fields absent from the ARB pack. Where both packs contain the same field, ARB wording wins; the desk wording remains an alternate in the generated overlay receipt. A complete ARB edition is `NATIVE_ARB`. A complete pair using one or more desk fields is `MACHINE_REVIEWED`, a legacy state name meaning machine-prepared and **not** human-reviewed. Incomplete pairs are `PENDING`. Missing or unknown provenance, an English leak, token drift or invalid structure is `FAILED`. No tool assumes ARB origin for an unlabelled field.

Every machine-prepared story page carries a short localized disclosure and an English-original link. The status, integrity manifest and newsroom receipt report counts for all four states per locale.

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

The receipt explicitly records `editorial_owner: "FCMO Publication Desk"`, `human_reviewed: false` and `network_translation: false`.

A deterministic checker cannot prove literary quality. Editorial equivalence remains the Publication Desk's responsibility and is reviewable through source control and the public evidence record.

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

- `site/data/i18n/<locale>/part-airlock.json` and historical numbered packs — ARB-authored locale fields;
- `site/data/i18n/<locale>/part-desk.json` — Publication Desk fields and per-record provenance;
- `i18n/ui/<locale>.json` — source-controlled UI catalogue;
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
