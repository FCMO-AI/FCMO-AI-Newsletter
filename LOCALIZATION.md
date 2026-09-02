# FCMO AI Newsletter curated localization contract

English is the **canonical semantic source** of the FCMO AI Newsletter. The native publication supports exactly three locales:

- `en` — English, canonical source;
- `es-419` — Latin American Spanish, curated translation;
- `zh-Hans` — Simplified Chinese, curated translation.

Browser extensions, operating-system translation, search-engine translation, or other third-party translation layers are outside this contract. They may translate the site independently, but they are not FCMO-native translations.

## What “curated” means

The Spanish and Chinese packs are model-curated, source-controlled publication artifacts. They are not generated at page view time, do not call Google Translate, DeepL, OpenAI, Anthropic, Microsoft Translator, or another translation endpoint, and are not silently replaced by a runtime fallback.

The packs are deliberately **not labelled human-reviewed**. A human-review claim may only be added after a qualified bilingual reviewer has actually reviewed that locale.

Translate intent rather than English syntax. Preserve:

1. evidence strength and uncertainty;
2. caveats and contrary evidence;
3. numbers, model/version identities, benchmark names, stable FCMO IDs, and URLs;
4. distinctions between demonstrated, claimed, inferred, and editorial interpretation;
5. technical terms where translation would make the meaning less precise.

A natural, shorter sentence is preferred to a literal translation that reads like translated English, but no translation may strengthen a research claim beyond the canonical source.

## Story coverage

Every canonical news record must have a curated translation of its reader-facing editorial story in both non-English native locales:

- `title`;
- `summary`;
- `why_it_matters`.

The current release contains 22 canonical briefs, therefore each curated locale pack must contain exactly 22 matching stable FCMO IDs. Build validation rejects missing, empty, shifted, or unchanged-English editorial fields.

The deep technical/evidence dossier remains the canonical English research record. When Spanish or Chinese is selected, the translated title, summary, and editorial consequence are shown natively and the deeper canonical dossier is preserved behind an explicit expandable **English canonical record** boundary. This avoids silently translating evidence-bearing technical prose in a way that could change epistemic meaning.

## Runtime behavior

Locale resolution is deterministic:

1. explicit `?lang=` parameter;
2. saved manual selection;
3. `navigator.languages` / browser preference;
4. English fallback.

All `es-*` browser locales resolve to `es-419`. All `zh-*` browser locales resolve to `zh-Hans`, because Simplified Chinese is the single native Chinese edition currently maintained. English remains directly selectable at all times.

The language control presents English as the canonical source and Spanish/Chinese as curated translations. A manual change persists locally and is reflected in the URL so a language-specific view can be shared.

## Source-control layout

- `site/data/i18n/es-419/part-*.json` + `ui.json` — curated Spanish editorial translations and UI catalogue;
- `site/data/i18n/zh-Hans/part-*.json` + `ui.json` — curated Simplified Chinese editorial translations and UI catalogue;
- `site/assets/curated-i18n.js` — deterministic presentation/runtime layer;
- `site/assets/curated-i18n.css` — language selector and canonical-record presentation;
- `tools/apply_curated_i18n.py` — build-time injection, coverage validation, provenance manifest, and integrity-manifest refresh.

The frozen Signal Field English release is assembled and validated first. Only after its canonical index hash passes is curated localization injected. The localized build records both the original canonical index SHA-256 and the final localized index SHA-256 under `data/i18n/manifest.json`.

## Publication gate

A release must fail if:

- either curated locale omits any canonical FCMO story ID;
- title, summary, or why-it-matters is absent or unchanged English;
- the locale pack was built against a different canonical editorial source hash;
- a runtime translation provider endpoint appears in the localization code or packs;
- the runtime exposes any native locale outside `en`, `es-419`, `zh-Hans`;
- the localized index cannot be traced back to the frozen canonical English index hash.

When a new story is added, its Spanish and Chinese editorial translations are part of the same publication obligation. Missing translations are a release defect, not an invitation to machine-translate at runtime.
