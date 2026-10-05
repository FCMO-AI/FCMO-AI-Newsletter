# Campaign 5 — L4 localization

**Branch:** `c5/l10n`  
**Scope:** localization completeness gate, story localization mapping, locale root routes, dates and their tests.

## Result

The release gate now checks every non-empty reader-facing prose leaf in `stories.v2` against the selected locale fields. A `COMPLETE` state with omitted leaves fails closed, and the failure reports complete/incomplete pair counts and missing-leaf counts for both locales. Pending-page detection checks for the localized notice inside a `.pending-panel`, so a copy of the pending label in the embedded UI catalogue no longer looks like a pending story.

The leaf audit also exposed two translated relationship summaries present in the locale packs but dropped by the story-layer adapter. The adapter now carries those localized summaries into `stories.v2`, includes their provenance/state in the l10n result, and the schema permits the structured localized relationship field. The checked-in `site/data/stories.v2.json` was regenerated from the current corpus at its existing `generated_at` value.

## Red-first evidence

- Before the gate change, a regression fixture declared `NATIVE_ARB` with `missing: []` while omitting evidence prose; the release gate passed. The test now fails that false-complete case and checks its per-locale incomplete and missing-leaf counts.
- Before the pending-panel change, a complete page containing the text `Traducción pendiente` in a script failed the gate. The gate now checks the rendered pending panel instead.
- A story-layer test confirms localized relationship summaries survive into `stories.v2`.

## Verification

- `python3 -m unittest discover -s tests`: **565 tests, 0 failures, 0 errors, 2 existing browser-dependent skips**.
- The focused relationship/schema and gate tests passed after the story-layer changes; the pending-panel and leaf-count regressions also passed after the final diagnostic change.
- `python3 -m compileall -q tools tests`: PASS.
- A fresh build from the current corpus and current locale packs passed the release gates: **13/13**, including `NO_FCMO_GROUP`.
- The current build reports `es-419: complete=41 incomplete=0 missing_prose_leaves=0` and `zh-Hans: complete=41 incomplete=0 missing_prose_leaves=0` (2,160 canonical prose leaves checked across both locales). The independent strict validator likewise reports 41/41 complete per locale.
- The generated `/es/` and `/zh/` roots exist and carry `lang="es-419"` and `lang="zh-Hans"`; the locale-root build test passes. The suite also passes the raw-enum and month-table checks, including rejection of `Sept` abbreviations.
- `git diff --check`: PASS.

## Evidence boundary

The campaign snapshot describes 18/22 incomplete pairs and roughly 454 missing leaves per locale on a 43-story set. That count did not reproduce on this branch and corpus: the current corpus has 41 live stories, and both the strict field-level validator and a fresh modern story-layer build report 41 complete per locale, with zero missing prose leaves. I report the measured current state rather than carry forward the older count. The strict validator reports two stale locale overlays for a non-live ID; they are ignored and do not affect live-story counts.

The build and gates were run locally. This report does not claim a production-site check, browser visual review, merge, or deployment. Those remain for the architect’s host rerun and the separate production/visual lanes.

Resumen: el gate ahora detecta hojas de prosa faltantes y las relaciones traducidas ya llegan al periódico; en el corpus actual hay 41/41 historias completas por idioma y pasan 13/13 compuertas.
