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

# Lane L28b

The complete implementation, evidence, public record contract and continuation
are in [REPORT-L28b.md](REPORT-L28b.md).

Resumen: cartas, ensayos y notas EN/ES/ZH por el dispatcher de proveedores, con
revisión humana, intents permanentes y registro público para Studio. Trabajo
local, sin push ni correo real; la prueba de producción queda pendiente.

## L11 — publicación protegida

Ver REPORT-L11-pub.md (evidencia histórica).

## L29 — integración local de campaña 5

Informe completo: [REPORT-L29.md](REPORT-L29.md), con las primeras ocho líneas
para Matías. Studio/translate y email-kit integrados, seam de aprobación →
intención → dispatcher → estado de Studio verificado y L27e corregido red-first.
Ramas antiguas auditadas; se integró sólo el trabajo único querido de publicación.

**Resumen:** 813 tests OK (4 omitidos), 14/14 gates por proveedor y release 7/7.
Sin push remoto, envío real ni Kit live. Chromium ausente: aceptación visual y
dogfood completo pendientes, sin omitir el navegador ni declarar producción.


## L30 — integración con escritores vivos (2026-10-07)

Entrega y comandos del arquitecto en [REPORT-L30.md](REPORT-L30.md).
Se integraron los 17 commits observados de main, conservando el ledger activo
allí: 71 registros, bytes idénticos al remoto. La migración aislada se difiere
hasta cambiar escritores y lectores juntos. Se adaptó NOT_ESTABLISHED sin
subir fuerza de evidencia y se reconstruyó el release derivado offline.
Corpus y estados remotos se conservan. Suite final: 814 tests OK (4 skipped);
release 7/7. Sin push ni escritura remota; navegador y producción quedan al
arquitecto.
