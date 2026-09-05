# FCMO AI Newsletter curated localization contract

English is the **canonical semantic source** of the FCMO AI Newsletter. The native publication supports exactly three editorial locales:

- `en` — English, canonical semantic source;
- `es-419` — Latin American Spanish, curated translation;
- `zh-Hans` — Simplified Chinese, curated translation.

Browser extensions, operating-system translation and third-party translation layers are outside this contract.

## What “curated” means

Spanish and Chinese are model-curated, source-controlled publication artifacts. They are generated before publication, never at page-view time, and are deliberately **not labelled human-reviewed** unless a qualified reviewer actually performs that review.

Translate intent rather than English syntax while preserving evidence strength, uncertainty, caveats, numbers, model/version identities, benchmarks, stable FCMO IDs, URLs, and the distinction between demonstrated, claimed, inferred and editorial interpretation. A translation may improve naturalness, but may not strengthen a research claim beyond the canonical English source.

Translation and review are separate operations. The model that produces a locale candidate is not treated as sufficient proof of editorial quality. `tools/review_localizations.py` independently compares the candidate with canonical English using deterministic invariants plus an MQM-style machine editorial review. Any Critical or Major finding blocks publication. Review receipts explicitly state `human_reviewed: false`.

## Coverage contract

Every canonical public record must have a curated translation for the reader-facing prose that the site renders, including:

- title, summary, why-it-matters and importance rationale;
- limitations and contradictory evidence;
- claim text and evidence-gap descriptions;
- reader-facing technical-dossier prose and relationship summaries;
- any other prose field explicitly present in the current declassified public schema.

Private ARB strategic implication fields are not part of the new public translation obligation because semantic declassification removes them before the corpus crosses the airlock. `tools/reconcile_locale_overlays.py` prunes previously translated fields that no longer exist in canonical public data so an old translation cannot resurrect declassified-away content.

Coverage is **dynamic, never hard-coded to a historical corpus size**. If English contains `N` stable FCMO IDs, Spanish and Chinese must contain exactly the same `N` IDs. Locale metadata, public brief JSON, stable development routes and the localization manifest must agree with that live set.

Count-bearing UI is formatted dynamically. A catalogue key must not bake in a corpus count such as `22 briefs`; growth of the corpus must not invalidate translation lookup.

English remains directly selectable and authoritative as the semantic source. Non-English dossier views are curated translations of that source, not a separate evidence record. The interface labels that relationship explicitly rather than falsely claiming translated technical prose is still English.

## Per-story freshness

Stable identity does not imply stable prose. A material update to an existing FCMO ID must invalidate its old translations.

`tools/translation_freshness.py` computes a digest of the exact reader-facing canonical prose projection for every stable record and stores it in `site/data/i18n/source-digests.json`.

Before translation, `--invalidate` removes locale overlays whose canonical digest changed. The ordinary translator therefore sees them as missing and regenerates them. After both locales are complete and reviewed, `--record` refuses to advance the digest manifest unless both locale ID sets exactly match canonical English.

This closes the prior failure mode where `translate_records.py` translated new IDs correctly but an existing ID could change in English while retaining stale Spanish/Chinese prose.

## Independent machine editorial review

`tools/review_localizations.py` records source and translation digests for each `{locale, FCMO-ID}` pair in `site/data/i18n/review-manifest.json`.

For a changed pair it checks, at minimum:

- exact preservation of numeric tokens;
- exact preservation of stable FCMO IDs;
- exact preservation of URLs embedded in translated prose;
- factual/semantic accuracy against canonical English;
- evidence-strength and uncertainty preservation;
- benchmark/model/version/identity fidelity;
- target-language fluency, terminology and style.

Provider review is chunked by story batches so unrelated stories do not create an avoidable context/output-budget coupling. A deterministic-only review mode exists only for migration/unit-test bootstrap and is explicitly not accepted as a reusable production language-review receipt.

## Runtime behavior

The app-shell locale resolution remains deterministic:

1. explicit `?lang=` parameter;
2. saved manual selection;
3. `navigator.languages` / browser preference;
4. English fallback.

All `es-*` browser locales resolve to `es-419`; all `zh-*` locales resolve to `zh-Hans`. The selected locale persists locally and is reflected in the URL.

The runtime performs **presentation lookup only** against committed packs. It contains no translation-provider endpoint and no generative fallback. A missing translation is a release defect.

Legal/disclosure text is also translated for readability. Where English is the governing legal wording, the translated block carries an explicit notice and a route back to the English version.

## Static newspaper routes

The autonomous Story layer additionally emits crawlable static routes:

- `/news/en/...` for `en`;
- `/news/es/...` for the `es-419` editorial translation, exposed to search engines with `hreflang="es"`;
- `/news/zh-hans/...` for `zh-Hans`.

Each Story page includes reciprocal language alternates and `x-default`. The static route is a distribution surface over the same curated locale pack, not a second translation pipeline.

## Source-control layout

- `site/data/i18n/es-419/part-*.json` + `ui.json` — curated Spanish prose and UI catalogue;
- `site/data/i18n/zh-Hans/part-*.json` + `ui.json` — curated Simplified Chinese prose and UI catalogue;
- `site/data/i18n/source-digests.json` — per-story canonical semantic freshness identity;
- `site/data/i18n/review-manifest.json` — independent machine-editor review receipts;
- `site/assets/curated-i18n.js` — deterministic presentation/runtime layer;
- `site/assets/curated-i18n.css` — language selector and translated-dossier presentation;
- `tools/apply_curated_i18n.py` — coverage validation, bundle injection, provenance manifest and integrity refresh;
- `tools/translation_freshness.py` — changed-existing-story invalidation and digest recording;
- `tools/review_localizations.py` — independent machine editorial quality gate.

The canonical English release is assembled and hash-verified first. Localization is injected only after that identity passes. The localized build records both the canonical and localized index SHA-256 values in `data/i18n/manifest.json`.

## Publication gate

A release must fail if:

- either curated locale omits a canonical FCMO ID or contains a stale/extra ID;
- locale record-count metadata differs from the live canonical corpus;
- public brief JSON or stable development routes differ from the canonical IDs;
- required reader-facing prose is absent, empty or unchanged English where translation is required;
- an existing translated record was built against an older per-story canonical digest;
- independent review reports a Critical or Major language error;
- a locale pack was built against a different canonical editorial digest;
- a count-bearing historical UI key is introduced;
- a runtime translation-provider endpoint appears;
- any native editorial locale outside `en`, `es-419`, `zh-Hans` is exposed;
- the localized index cannot be traced to the frozen canonical English index hash.

A new or materially changed story and its curated native translations are one publication obligation. The gate fails closed rather than publishing a partial language edition.
