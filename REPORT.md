# Reparación de los seis fallos de main

Rama: `fix/main-red-6`. Base local: `ce8e4efa` (`origin/main`). No se hizo push ni despliegue. No se modificaron el corpus, el ledger ni archivos generados de publicación.

## Commits de implementación

- `1c05fbd3` — Preserve first publication clocks in shallow story builds
- `49102c90` — Isolate essay discovery tests and complete native UI labels

## Causas y cambios

1. **Ensayo y descubrimiento** — `EssayBuildTests.test_build_emits_piece_pages_and_discovery_surfaces` suponía que `es/data/search.json` era el índice entero. El constructor ya conserva los ensayos en fragmentos adicionales y la página de búsqueda los referencia mediante `data-shards`. No había un filtro que eliminara el ensayo. El test ahora usa `contracts/fixtures/stories.v2.json` y `newsroom-status.fresh.json`, fuerza fragmentación con un presupuesto pequeño y recorre exactamente los archivos referenciados por el HTML final. Exige que el ensayo aparezca una sola vez con su ruta completa, fuera del primer fragmento. Las verificaciones de páginas, feeds, sitemap, notas, fuentes y superficies para agentes permanecen. Los otros tests del ensayo también usan estos fixtures para quedar independientes del corpus diario.

2. **Etiquetas de UI** — `UICatalogs.test_every_reader_facing_enum_has_a_label` detectaba correctamente una omisión real: `CLAIMED_PROVIDER_OPERATING_TERMS`. Tras añadirla, el mismo test expuso ocho omisiones adicionales: `contradiction_unresolved`; regiones `California`, `Iran`, `Jiangsu`, `Latin America`, `us`; idiomas fuente `es-419`, `zh-Hant`. Se añadieron las nueve etiquetas en cada catálogo, con traducciones reales. Los idiomas fuente describen evidencia recibida; no habilitan nuevas ediciones del periódico. Se conserva íntegro el gate de cobertura de enums y las comprobaciones de idioma, placeholders y glosario.

3. **Fecha de primera publicación** — los tres tests `RepositoryStoryLayerTests.test_first_publication_comes_from_the_ledger`, `RepositoryStoryLayerTests.test_ledger_is_frozen_and_idempotent` y `TemporaryCorpusTests.test_ledger_from_history_equals_the_contract_fixture` suponían que una identidad todavía no congelada debía tomar siempre la fecha del archivo v1 actual. El contrato documentado ya priorizaba el mínimo histórico. Las expectativas ahora respetan esa prioridad, sin fijar una fecha nueva del corpus diario. Se conservan las comparaciones exactas de todas las entradas congeladas y del fixture histórico, las redirecciones y la idempotencia. Los nuevos tests aislados construyen dos commits en un repositorio temporal, con corpus y ediciones nativas de prueba: primera publicación, refresh posterior, reconstrucción, congelamiento e idempotencia. Así el comportamiento causal tiene un oracle fijo independiente de la producción.

4. **Reconstrucción sin historial** — `ShallowCheckoutTests.test_previous_v2_restores_what_history_would` detectaba un bug real. El código usaba el documento anterior para restaurar registros ausentes, pero ignoraba su `first_published_at` para historias presentes que aún no tenían ledger. Tomaba el reloj posterior de v1 y cambiaba el orden, incluyendo el primer elemento señalado en el brief. `StoryInputs` ahora conserva los relojes válidos de v2. Tanto la composición como el avance del ledger usan la prioridad: ledger congelado → historial completo → v2 anterior → v1 actual → reloj candidato. El reloj candidato sigue sin congelarse para una identidad inédita. Las entradas existentes nunca se reescriben.

## Ledger contra historial: cuál tiene razón

Las **49 entradas congeladas coinciden exactamente** con las primeras fechas del historial tras la normalización contractual a segundos. Se comprobó con `history_first_published`; la lista de discrepancias resultó vacía. No hay una entrada congelada equivocada que corregir.

Las cinco identidades discrepantes **no están en el ledger**: `FCMO-710E8BDAF4B5`, `FCMO-503C5DEC490A`, `FCMO-2B000C93D92A`, `FCMO-727CB05A3E39`, `FCMO-28A7A138B4E8`. El commit público `2f7de900` ya contiene sus fechas anteriores. Cuatro tienen la primera fecha del 8 de octubre a las **03:00 CDMX**; `FCMO-503C5DEC490A`, del 7 de octubre a las **20:00 CDMX**. El archivo v1 actual muestra para las cinco el 8 de octubre a las **18:49 CDMX**. Según el contrato de este repositorio, el mínimo histórico tiene razón; el reloj del refresh posterior no sustituye una primera publicación. Esto prueba metadatos del historial público, no el instante de visibilidad en el origen externo.

## Evidencia antes y después

- Baseline de los tres módulos: **77 tests, 6 fallos**, observados antes de corregir código o catálogos. Log local: `/tmp/nl-main-red-baseline.log`.
- El test del ensayo con fixtures y fragmentación forzada también falló antes de corregir su lectura del índice: `/tmp/nl-main-red-essay-fixture-before.log`.
- Los nuevos tests `test_previous_v2_preserves_history_without_a_frozen_ledger` y `test_shallow_ledger_uses_previous_v2_instead_of_a_later_v1_clock` fallaron con el código base y pasaron después. Log previo: `/tmp/nl-main-red-history-regression-before.log`.
- `test_earliest_history_wins_over_a_later_current_publication` y `test_frozen_ledger_wins_over_history_and_previous_v2` preservan explícitamente los límites de autoridad y congelamiento.
- Se armó un candidato temporal con la nueva etiqueta y se inspeccionó el DOM final de las tres rutas nativas: cada una contiene su etiqueta traducida, sin mostrar el enum crudo. Log: `/tmp/nl-main-red-label-dom.log`.

## Aceptación

El workflow mencionado en el brief, `.github/workflows/test.yml`, no existe en esta base. El workflow real de CI es `.github/workflows/contract-tests.yml`: compila herramientas/tests y ejecuta discovery con `FCMO_SKIP_STATEFUL_REFRESH_ORACLES=1`. PyYAML 6.0.2 y age ya estaban instalados; no se instalaron dependencias ni se usó la red externa. El intérprete local es Python 3.13.5; el workflow declara Python 3.12, cuya ejecución queda a CI.

### Tres módulos afectados

Comando desde la raíz:

```sh
PYTHONPATH=tests python3 -m unittest test_essay_build test_localization_completeness test_story_layer -v
```

Cola real:

```text
test_unrecorded_duplicates_are_still_merged (test_story_layer.TemporaryCorpusTests.test_unrecorded_duplicates_are_still_merged) ... ok
test_upstream_withdrawal_needs_no_human (test_story_layer.TemporaryCorpusTests.test_upstream_withdrawal_needs_no_human) ... ok

----------------------------------------------------------------------
Ran 77 tests in 32.038s

OK
routes=210 feeds=57 redirects=198 js_bytes=3172
routes=210 feeds=57 redirects=198 js_bytes=3172
routes=210 feeds=57 redirects=198 js_bytes=3172
```

### Regresiones aisladas y ensayos

```sh
python3 -m unittest tests.test_story_layer_history tests.test_essay_build -v
```

Cola real:

```text
test_semantic_renderer_covers_node_types_and_escapes_text (tests.test_essay_build.EssayBuildTests.test_semantic_renderer_covers_node_types_and_escapes_text) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.785s

OK
routes=210 feeds=57 redirects=198 js_bytes=3172
routes=210 feeds=57 redirects=198 js_bytes=3172
routes=210 feeds=57 redirects=198 js_bytes=3172
```

### Compilación

`python3 -m compileall -q tools tests` → código de salida 0, sin salida.

### Suite completa de CI

```sh
FCMO_SKIP_STATEFUL_REFRESH_ORACLES=1 python3 -m unittest discover -s tests -v
```

Resumen final real:

```text
Ran 852 tests in 1990.706s

OK (skipped=7)
```

Cola real del log (los mensajes de servicios, envíos y reglas provienen de mocks de los tests; no acreditan cambios de estado externos):

```text
PIECE FCMO-P-a94461245e02 es-419 QUEUED
PIECE FCMO-P-a94461245e02 zh-Hans QUEUED
PIECE INTENT READY keys=3
PIECE FCMO-P-a94461245e02 en SKIP
PIECE FCMO-P-a94461245e02 es-419 SKIP
PIECE FCMO-P-a94461245e02 zh-Hans SKIP
Studio user service enabled and active. Rollback: sh studio/host-ops/rollback.sh
Active protections verified. Rollback receipt: /tmp/tmpdhz2p0wm/rules.json
Previous ruleset state restored and verified.
routes=201 feeds=57 redirects=198 js_bytes=3172
```

### Diff contra main

```sh
git diff --stat origin/main
```

Cola real:

```text
 REPORT.md                         | 278 +++++++++++++++++++-------------------
 i18n/ui/en.json                   |   9 ++
 i18n/ui/es-419.json               |   9 ++
 i18n/ui/zh-Hans.json              |   9 ++
 tests/test_essay_build.py         |  36 +++--
 tests/test_story_layer.py         |  13 +-
 tests/test_story_layer_history.py | 102 ++++++++++++++
 tools/story_layer.py              |  24 ++--
 8 files changed, 321 insertions(+), 159 deletions(-)
```

`git diff --name-only origin/main -- site release-src release-overlay corpus` → sin salida. Ningún archivo generado de publicación cambia.

## UNVERIFIED

Omitidos por los guards existentes, sin modificar ni debilitar ningún test:

- `setUpClass (harness.test_harness_tools.BrowserRunTests)` — 'playwright not reachable through NODE_PATH'
- `test_fixture_with_horizontal_overflow_fails_the_real_browser_oracle (test_ci_visual_gate.CiVisualGateTests.test_fixture_with_horizontal_overflow_fails_the_real_browser_oracle)` — 'Playwright/Chromium is not installed'
- `test_generador_deriva_y_crece (test_refresco_diario.RefrescoDiario.test_generador_deriva_y_crece)` — 'stateful refresh oracles run after regeneration in the autonomous newsroom lane'
- `test_refresco_entero_publica_la_historia_nueva (test_refresco_diario.RefrescoDiario.test_refresco_entero_publica_la_historia_nueva)` — 'stateful refresh oracles run after regeneration in the autonomous newsroom lane'
- `test_todo_lo_publicado_tiene_ediciones_nativas (test_refresco_diario.RefrescoDiario.test_todo_lo_publicado_tiene_ediciones_nativas)` — 'stateful refresh oracles run after regeneration in the autonomous newsroom lane'
- `test_absent_renderer_fails_closed (test_studio_preview.PreviewIdentity.test_absent_renderer_fails_closed)` — 'Renderer integration is present; exercised by byte-identity test.'
- `test_the_real_build_passes_the_first_viewport_oracle (test_v4_mobile_first_viewport.OracleInBrowserTests.test_the_real_build_passes_the_first_viewport_oracle)` — 'Playwright module does not resolve from this checkout'

Python 3.12 y los checks reales de navegador quedan sin verificar en este entorno.

No se verificó un despliegue ni el origen público: esta lane prohíbe red y push. Las inspecciones locales de DOM no acreditan rendering en navegador real.

## NEEDS.md

No se requirieron cambios fuera del alcance. El `NEEDS.md` heredado se preservó sin cambios; esta lane no añadió solicitudes.

## KNOWN GAPS

No se añadieron mecanismos de publicación ni se adelantó el ledger manualmente. La promoción real corresponde a la integración y sus gates de publicación existentes. El resultado de esta lane se limita al software y las verificaciones locales descritas.
