# FCMO AI Newsletter curated localization contract

English is the **canonical semantic source** of the FCMO AI Newsletter. The native publication supports exactly three locales:

- `en` — English, canonical semantic source;
- `es-419` — Latin American Spanish, curated translation;
- `zh-Hans` — Simplified Chinese, curated translation.

Browser extensions, operating-system translation and third-party translation layers are outside this contract.

## What “curated” means

Spanish and Chinese are model-curated, source-controlled publication artifacts. They are generated before publication, never at page-view time, and are deliberately **not labelled human-reviewed** unless a qualified human reviewer actually performs that review.

Airlock v2 adds an independent model-editor pass after generation. Translation generation and approval are separate operations: the second pass sees canonical English plus the candidate translation and must reject factual drift, omissions, stronger/weaker evidence language, altered identifiers/numbers or material terminology errors. Its PASS receipt is bound to the SHA-256 digests of both source and translation, so any later change invalidates the approval automatically.

Translate intent rather than English syntax while preserving evidence strength, uncertainty, caveats, numbers, model/version identities, benchmarks, stable FCMO IDs, URLs, and the distinction between demonstrated, claimed, inferred and editorial interpretation. A translation may improve naturalness, but may not strengthen a research claim beyond the canonical English source.

## Coverage contract

Every canonical record must have a curated translation for **every reader-facing prose field that is present in the current public English contract**, including:

- title, summary, why-it-matters and importance rationale;
- limitations and contradictory evidence;
- claim text and evidence-gap descriptions;
- reader-facing technical-dossier prose and public relationship summaries.

The list is intentionally defined by the current canonical public object rather than by private upstream schema. If the semantic airlock reclassifies a formerly public field as private, `tools/prune_locale_packs.py` removes that stale overlay field before the next release so a translation cannot preserve prose English no longer publishes.

Coverage is **dynamic, never hard-coded to a historical corpus size**. If English contains `N` stable FCMO IDs, Spanish and Chinese must contain exactly the same `N` IDs. Locale metadata, public brief JSON, stable development routes and the localization manifest must agree with that live set.

Count-bearing UI is formatted dynamically. A catalogue key must not bake in a corpus count such as `22 briefs`; growth of the corpus must not invalidate translation lookup.

English remains directly selectable and authoritative as the semantic source. Non-English dossier views are curated translations of that source, not a separate evidence record.

## Runtime and indexed routes

Locale resolution inside the reading application remains deterministic:

1. explicit `?lang=` parameter;
2. saved manual selection;
3. `navigator.languages` / browser preference;
4. English fallback.

All `es-*` browser locales resolve internally to `es-419`; all `zh-*` locales resolve to `zh-Hans`. The selected locale persists locally and is reflected in the URL.

The runtime performs **presentation lookup only** against committed packs. It contains no translation-provider endpoint and no generative fallback. A missing translation is a release defect.

Airlock v2 additionally emits crawlable stable story entry routes:

- `/en/developments/<FCMO-ID>.html`
- `/es/developments/<FCMO-ID>.html` — public web language code `es`, backed by editorial locale `es-419`;
- `/zh-hans/developments/<FCMO-ID>.html` — backed by editorial locale `zh-Hans`.

Those shells carry canonical/hreflang and localized metadata before resolving into the SPA reader. `x-default` points to English.

Legal/disclosure text is also translated for readability. Where English is the governing legal wording, the translated block carries an explicit notice and a route back to the English version.

## Source-control layout

- `site/data/i18n/es-419/part-*.json` + `ui.json` — curated Spanish prose and UI catalogue;
- `site/data/i18n/zh-Hans/part-*.json` + `ui.json` — curated Simplified Chinese prose and UI catalogue;
- `site/data/i18n/review-ledger.json` — digest-bound independent-editor PASS receipts after Airlock-v2 activation;
- `site/assets/curated-i18n.js` — deterministic presentation/runtime layer;
- `site/assets/curated-i18n.css` — language selector and translated-dossier presentation;
- `tools/prune_locale_packs.py` — removes stale fields no longer present in canonical public English;
- `tools/translate_records.py` — generates missing translations atomically;
- `tools/review_translations.py` — independent editorial QA for changed source/translation pairs;
- `tools/validate_translation_reviews.py` — deterministic, network-free verification that every active PASS still matches current bytes;
- `tools/apply_curated_i18n.py` — coverage validation, bundle injection, provenance manifest and integrity refresh.

The canonical English release is assembled and hash-verified first. Localization is injected only after that identity passes. The localized build records both canonical and localized index SHA-256 values in `data/i18n/manifest.json`.

## Publication gate

After autonomous-newsroom activation, a release must fail if:

- either curated locale omits a canonical FCMO ID or contains a stale/extra ID;
- locale record-count metadata differs from the live canonical corpus;
- public brief JSON or stable development routes differ from the canonical IDs;
- required reader-facing prose is absent, empty or unchanged English;
- a locale pack was built against a different canonical editorial digest;
- an independent-review PASS is absent, stale, or reports any Major/Critical error;
- a count-bearing historical UI key is introduced;
- a runtime translation-provider endpoint appears;
- any native locale outside `en`, `es-419`, `zh-Hans` is exposed;
- the localized index cannot be traced to the frozen canonical English index hash.

A new story and its curated native translations are one publication obligation. The gate fails closed rather than publishing a partial language edition.
