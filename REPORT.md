# L25 — refreshed Story corpus expectations

Updated the first-publication ledger only through `tools/story_layer.py ledger`. It added `FCMO-045BB8282222` and `FCMO-5B5B447325A8`, each at the first publication time recovered from repository history (`2026-10-04T06:29:30Z`); the ledger now has 46 entries and a subsequent `--check` reports zero changes. The contract fixture was synchronized from that generated ledger.

The Story and ingest tests now reflect the upstream CR L21 acceptance: 46 Story objects, 43 live, 1 withdrawn and 2 merged. Both repaired records normalize and publish; no live-corpus quarantine is expected. `EVENT_AT_INVALID` coverage remains through a fixture-derived record with a malformed `event_at`. The freshness oracle now uses the repaired September 30 event date, so corpus state is lagging rather than stale. The static paper build produced 129 Story routes: 43 each for EN, es-419 and zh-Hans. Airlocked locale sync and validation report all 43 complete in both locales.

Regenerated the canonical release source, newsroom surfaces/status, frozen overlay and paper receipt through repository tools. Added labels for the corpus's `fcmo_fallback` media enum in all three UI catalogs. All seven release gates pass.

Verification: `python3 -m unittest discover -s tests` — 603 passed, 3 skipped; paper build — 531 total routes / 129 Story routes; `tools/verify_release.py` — 7/7 gates passed. The two new downstream public-research receipts were generated offline and record zero source URLs reopened; no new source re-research is claimed. These are local build/release checks; no deployment or live-origin verification was performed.

**Resumen:** El ledger y las pruebas ya reflejan 43 historias activas; se conservó la cuarentena sintética para fechas inválidas. La compilación produjo 129 rutas localizadas y las siete compuertas pasaron. No se desplegó.

## L28a — Studio: español, traducciones y correo

Entrega de esta lane: [REPORT-L28a.md](REPORT-L28a.md). Se implementaron el botón
ES→EN/ZH, controles de estructura y procedencia, revisión humana obligatoria y
la intención de correo con hook para L28b. Los tests específicos e integración,
los 14 gates y la integridad de release pasan. La aceptación visual y el dogfood
completo siguen pendientes de Playwright, Chromium y axe-core. Sin push.

**Resumen L28a:** código probado localmente; no se publicó ni se envió correo.
La verificación completa en navegador permanece abierta.
