# Studio ready — acceso, bundle y vista previa

Cambios locales en `fix/studio-ready`, sin push ni cambios al servicio o a producción.
El acceso normaliza NFD, elimina marcas Unicode y convierte a minúsculas en la
pantalla, el servidor y el alta por CLI. Los alias comparten cuenta, sesiones,
bloqueo por intentos y auditoría; las contraseñas conservan sus bytes.

## Bundle reproducible sin descargas

`node studio/web/build.mjs` reconstruye `dist` y su manifiesto. Este entorno no
contiene esbuild ni ProseMirror en node_modules. El fallback reutiliza el bundle
compilado que ya estaba en el repositorio, comprueba su SHA-256 y los hashes de
las dependencias/fuentes, e inserta la función de acceso actual sin minificar.
Concatena el CSS actual y copia fuentes locales. No incorpora dependencias nuevas.

El fallback está deliberadamente acotado al acceso y al CSS: rechaza cambios en
otros módulos o dependencias para no acreditar código viejo con hashes nuevos.
La ruta normal con esbuild sigue disponible. `bundle_ready=True`; dos builds
consecutivos producen los mismos bytes. El negativo de drift del editor sigue
cerrado. Falta la inspección visual real del bundle en escritorio y teléfono.

## Perfil y tiempos

Comando reproducible con stores temporales, sin servicios ni transporte remoto:

```sh
python3 -m tests.harness.studio_preview_profile --baseline-ref 25c64214
```

| Renderer | Primera vista previa | Preparación | Repetición desde caché |
| --- | ---: | ---: | ---: |
| Referencia 25c64214 | 33,410 s | — | 0,000445 s |
| Studio, sin preparación explícita | 2,687 s | — | 0,000480 s |
| Studio, preparado | 2,501 s | 0,151 s | 0,000831 s |

La primera medición de un borrador también pasó de 32,535 s a 2,067 s. El objetivo
local de menos de 10 s se cumple. Estos son tiempos del entorno de esta lane;
no constituyen una medición del servicio instalado ni una promesa bajo toda carga.

cProfile atribuyó 168,942 de 175,375 s instrumentados a `_topic_links`, dentro de
un build de 1896 rutas. Recalculaba la pertenencia al corpus para cada vecino de
cada página. Studio indexa esa pertenencia una vez por build y cachea el HTML de
vecinos. Cuenta cada valor una vez por historia aunque se repita; conserva exclusiones
por nombre/slug, orden en empates y límites. El build completo, assets y gates se mantienen. La regresión
compara todos los archivos del árbol con el PaperBuilder original, byte por byte.

Las plantillas son módulos Python; no existe un compilador Jinja separado.
Al iniciar Studio se importan para preparar el caché de bytecode de Python.
El trabajo dominante eliminado es el recálculo de taxonomías. La preparación
rechaza un timeout de 10 s con un mensaje acotado, sin publicar diagnósticos.

## Batería y pruebas

La batería abre una sesión local aislada y mide un GET autenticado de una pieza
recién creada antes de arrancar Playwright. Sólo una respuesta 200 con el ensayo
puede fijar el presupuesto: `ceil(2 × segundos × 1000 + 5000)` ms. Por ejemplo,
50 s producen 105000 ms. El timeout llega a los frames de vista previa y revisión,
a las regresiones y al recibo de aceptación. La medición no conserva credenciales.

Se observaron fallos antes de corregir cada defecto: alias HTTP rechazados,
bloqueo evadido con alias, alta con acento inválida, build sin esbuild rechazado,
renderer sin índice y ruta estricta sin caché, y funciones de medición inexistentes.
El test de login web también falla contra la fuente de referencia (`matías` en
vez de `matias`) y pasa con la fuente final. No se debilitaron aserciones existentes;
la identidad de publicación se amplió al árbol completo.

Comandos de aceptación:

```sh
python3 -m unittest discover -s tests -p 'test_studio*' -v
python3 -m unittest tests.test_studio_bundle tests.test_studio_auth tests.test_studio_renderer_cache tests.test_studio_journey_timing
node --test studio/web/test/login.test.mjs studio/web/test/webp.test.mjs
node studio/web/build.mjs
python3 -c 'from studio.server.bundle import ready; print("bundle_ready=" + str(ready(".")))'
python3 -m studio.server.render_preview --warm
node --check studio/web/dist/app.js
python3 -m py_compile studio/server/auth.py studio/server/preview.py studio/server/render_preview.py studio/server/__main__.py tests/harness/studio_host_journey.py tests/harness/studio_preview_profile.py
git diff --check
```

Aceptación final: **101 tests en 534,555 s, OK (skipped=1)**. Se ejecutó la
suite pedida con `-v` para identificar los casos en la evidencia. La primera
pasada completa ejecutó 100 tests en 537,700 s y tuvo un único error: el fixture
nuevo de medición declaraba un Origin distinto al listener local. Se corrigió el
Origin del fixture, conservando CSRF/origen y las aserciones. Sus dos tests pasan
individualmente y en la repetición completa final. El skip preexistente está
acotado al negativo de renderer ausente, cuya integración ya está presente.
Pruebas específicas: 18/18; login y WebP en Node: 2/2. Construcción offline,
bundle_ready, preparación, sintaxis JS/Python y whitespace pasan.
`npm test --prefix studio/web` no queda verde: docmodel requiere el paquete
ProseMirror ausente; login y WebP sí pasan. El probe de navegador termina con
`BROWSER_UNAVAILABLE`, código 2: no está disponible el módulo Playwright.

## Commits de implementación

- `5ac4b8bc` — Normalize Studio login and rebuild the offline browser bundle
- `37f16a75` — Cache Studio renderer taxonomy work and warm compiled templates
- `c29e23cd` — Derive Studio browser preview budgets from measured rendering

Los commits llevan el crédito Codex requerido. El cierre documental también
incluye el rechazo acotado cuando la preparación supera 10 segundos.

## Fronteras pendientes

No se ejecutó la batería visual completa ni se inspeccionaron sus frames nuevos.
No se instaló ni reinició el servicio y no se comprobó el host de Javier ni el
origen público. El documento STUDIO-LIVE.md solicitado no está disponible en esta
sesión; se leyó REPORT-STUDIO-LIVE.md del repositorio. La mejora común del renderer
canónico y la repetición visual están registradas en NEEDS.md.

---

# L41 — admisión nativa y desbloqueo de publicación

## Resultado

Reparación local en `c5/l41-publish`, sin push. El árbol compuesto contiene
86 historias live con sus tres ediciones completas; Story v2 conserva además
1 retirada y 2 merges. Las cinco identidades con inglés residual quedan retenidas
con motivos explícitos en `release-src/data/publication-admission.json`.
El corpus recibido conserva el material para reparación y reintento automático:
backlog recibido es-419=4, zh-Hans=3, unión=5; backlog publicado=0.

La aceptación completa **no está demostrada**: falta Playwright/Chromium.
`ops/publish.py --check` termina con código 2 exactamente en el oracle de navegador,
después de suite, integridad, construcción, agent hygiene y los 14 gates verdes.
No se consultó ni modificó producción. El seguimiento autónomo real requiere
merge autorizado, deploy y ciclos posteriores observados por el verificador.

## Base y commits

El worktree ya existía sobre `79055f8` (L42) y el refresh público `2f7de90`.
`12168eb` ya había integrado L39, incluidos sus tres fixes; se conservó ese merge.

| Commit | Trabajo |
|---|---|
| `d540933` | Red first: vocabulario, hold/recovery y oracle antes del commit; 3 tests, 3 errores antes del fix. |
| `64d91be` | Red first: titular con evidence, binding vacío y rutas acentuadas; 3 tests, 1 fallo y 2 errores. |
| `01f8217` | Admisión, vocabulario, oracle independiente, etiquetas y corrección de gates; primera composición. |
| `5c977f0` | Refresh con ediciones reales de fixture; conservación de investigación pública en la composición. |
| `252892c` | Carry probado a través de ingest/sync/reconcile/ACK; tier preservado incluso con otro score. |
| `02c1531` | Overlay de recuperación sincronizado y su regeneración/check antes del commit automático. |
| `01440c4` | Oracle de publicación contra la versión inglesa comprometida; no confunde un update recibido con su carry. |

Todos los commits de L41: Codex <noreply@openai.com>. Ningún push, fetch ni cambio
a main/origin del repositorio de trabajo. Los remotes de pruebas fueron locales.

## Clases cerradas y decisiones

- **2 — tiers:** diez valores upstream, sus labels EN/ES/ZH y enums en los contratos.
  El tier procede del registro; una prueba recorre los diez con score=6 y conserva
  cada etiqueta. Useful vuelve a normalizarse y publicarse.
- **3 — tipos y labels:** `reproduction_or_audit`, `signal_or_leak` y `other`
  permanecen como tipos canónicos distintos: una auditoría y una señal no tienen
  la misma función informativa que un paper o un lanzamiento. Se renderizan labels
  naturales; se completaron también claim labels, regiones e idiomas observados.
  Tier y tipo se conservan como metadata opcional de Story y se muestran en sus facts.
- **4 — admisión:** ingest y Story usan la misma decisión por pares fuente/overlay.
  FAILED/PENDING retiene la versión recibida. Una versión previa se lleva adelante
  sólo si sus dos ediciones y bindings aún validan; sync conserva esos packs.
  ACK y salud de publicación juzgan el inglés efectivamente publicado;
  `--all-corpus` sigue midiendo la deuda de reparación recibida.
  Se ejecuta `verificar_traduccion.py` antes del commit. No se modificó ese oracle,
  el gate ENGLISH_LEAK ni se generaron traducciones de producción.
- **5 — oracle:** recuento independiente de hojas internas, comparación con inglés
  y detección de prosa inglesa; NOW deriva del corpus más grace+1h. Las assertions
  de receipts distinguen material recibido de historias realmente publicadas.
- **6 — gates/Studio:** BINDING_COMPLETE confundía un titular terminado en
  “evidence — FCMO AI” con un binding vacío. Se corrige la interpretación y se
  conservan negativos para labels vacíos, incluso separados por tags.
  API y lector ahora comparten slug Unicode para las organizaciones acentuadas;
  AGENT_LAYER valida los destinos. Los dos recorridos completos de Studio pasan.
- **Coherencia adicional:** apareció el overlay de recuperación de 50 historias
  frente a la fuente nueva de 86: tres compuertas de release fallaban. Se regeneró
  sin relajar hashes y se añadió su freeze/check al refresh. Pages sigue siendo
  el único renderer de producción y el único writer de despliegue.

Se conservaron los receipts públicos reutilizables para 85 historias admitidas;
la nueva historia recibió el pase offline. No hubo acceso externo a fuentes,
traducción, ARB privado ni secretos. L42 permanece: no cambios a search_index.py,
SEARCH_JS, presupuesto de búsqueda ni implementación de documentos llms.
La nota al origen está en [c5/CR-L41-upstream.md](c5/CR-L41-upstream.md): siete hojas
con fuga en cinco identidades. El snapshot examinado muestra claims[0].text y
technical.strongest_baseline también en zh-Hans; difiere de los summaries indicados
para esas dos identidades en el brief inicial. La nota refleja los bytes observados.

## Evidencia de aceptación

Logs locales ignorados en `_audit/l41/`; el verificador debe repetirlos en el host.

| Comprobación | Resultado |
|---|---|
| `python3 -m unittest discover -s tests` (ejecutado por ops --check) | 842 tests, 0 failures, 0 errors, 4 skipped; 769.433 s. |
| Desde tests: localization_completeness + story_layer + refresco_diario | 76 tests, OK; 59.041 s. |
| Native admission + gate corpus regressions | 7 tests, OK. |
| Tier/hold/recovery dirigidos finales | 4 tests, OK. |
| Carry con sync/reconcile/ACK | 7 tests, OK. |
| Workflow de recovery + admisión tras el cambio final | 29 tests, OK. |
| Oracle de localización publicado + admisión, cierre | 41 tests, OK; 2.870 s. |
| StudioIntegration + BareRemote, recorridos completos | 2 tests, OK; 201.413 s. |
| `verificar_refresco.py` | 87 historias; la sintética llega a EN/ES/ZH y discovery; oracle de traducción pasa antes del freeze. |
| `verificar_traduccion.py` sobre el árbol refrescado | 86 completas, pending=0; recientes materiales dentro del SLO. |
| `tools/verify_release.py` | 7/7, incluido NO_FCMO_GROUP; 86 registros y 0 traducciones pendientes. |
| `tools/gates/run_all.py` sobre candidato actual | 14/14; AGENT_LAYER y BINDING_COMPLETE pasan. |
| Paper | 906 rutas, 57 feeds, 596 redirects; JS 3172 B. |
| `ops/publish.py --check --out …` | Exit 2: BROWSER_UNAVAILABLE después de las comprobaciones anteriores. |
| HTML final de Useful y reproduction_or_audit | Seis páginas EN/ES/ZH contienen sus etiquetas en el texto del DOM; evidencia `dom-proof.json`. |
| Ready receipt, comprobación de cierre | OK, 906 rutas; candidato 8660fcb2638c. |
| `git diff --check` | Limpio. |

La suite general comenzó antes del último ajuste del workflow de recovery;
los 29 tests dirigidos posteriores cubren ese cambio, y las siete compuertas
verifican el nuevo overlay. No se presenta la ausencia de navegador como aceptación
visual. Las cuatro omisiones incluyen las pruebas que dependen de navegador/axe
no disponibles y el caso del renderer retirado cubierto por la integración real.

## Clase 6: alcance del diagnóstico visual y de Studio

No se cambió CSS ni el presupuesto móvil. El brief del host midió h1-top
EN/ES=296 px, ZH=299 px, dentro de max=460 y target=420. El oracle evalúa gates
además del viewport: el candidato inicial falla BINDING_COMPLETE por el titular
válido. Es un falso positivo del gate, no evidencia de un h1 demasiado bajo.
Las mediciones son del brief, no tomadas aquí. No hay screenshot local ni prueba
visual final: Playwright no resuelve. Debe ejecutarse el oracle móvil con
`--print-measurements` y conservar frames EN/ES/ZH en el host.

En un checkout coherente del commit inicial `12168eb`, Studio superó review/request
pero se detuvo al publicar por BINDING_COMPLETE. Aquí no se reprodujo el 409
pre-review del host bajo esas mismas condiciones. Los recorridos finales sí
alcanzan publicación local, incluidos revisión por la otra persona y repositorio
bare; no se afirma haber publicado en GitHub ni en el sitio público.

## Entorno y continuación

COMMON.md y los directorios de herramientas/temporal indicados en el brief no
existen en este entorno. No hubo permiso de filesystem para crear el temporal
solicitado. Se aplicaron las reglas comunes del mensaje. El primer discover
recibió ese TMPDIR inexistente y Python hizo fallback al temporal del sistema;
se corrigió después a `_audit/l41/tmp` dentro del worktree para las pruebas
restantes. Ese primer discover no es la prueba final de aceptación.

Continuación: con las herramientas del host, repetir el comando de aceptación
de ops del brief, comprobar los cuatro tests omitidos aplicables y el oracle
móvil/frames. Verificar el upstream note y ejecutar las suites sin flags que
omitan los oracles de refresh. Sólo el operador decide merge/push. Después:
Deploy, origen público y ciclos automáticos repetidos siguen pendientes.

**Resumen en español:** se reparó el vocabulario y la admisión por historia;
86 historias completas se construyen y cinco esperan reparación upstream.
Suite y gates pasan. Falta demostrar navegador y producción; no se hizo push.

---

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

---

# PR #74 / #71 sync onto main (#75)

## Commits

- `d86cadcb` — Merge main into Studio readiness branch (`sync/studio-ready`). The only conflict was `REPORT.md`; the Studio report and #75 report are both retained. Generated publication files came from main through the merge; no publication output was hand-edited.
- `22a15b86` — Merge main into protected publish gate branch (`sync/f4-deploy-red`). `REPORT.md` and `tests/test_story_layer.py` were the only conflicts. Both reports were retained, and the test file merged the #75 clock assertions with #71's quarantine regression.
- `95b84294` — Clarify retained history-derived publication output in the #71 report.

## #71 overlap decisions

- `beb01a26`: partly superseded by main commit `49102c90` for the overlapping UI labels. Its independent quarantine-test correction remains.
- `918102f2`: remains useful; #75 does not change the localization test contract allowing California as a proper name in Spanish.
- `c3567c32`: the shallow-clock behavior overlaps main commit `1c05fbd3`, while the full-history checkout remains the stronger `--history-git` source. Its five history-derived article pages remain valuable outputs and are committed output from that history-aware build; they were not hand-edited.
- `5337890d`: remains useful; #75 does not modify publish-gate runtime optimization, candidate reuse, or workflow timeout budgets.

No #71 implementation commit was wholly dropped. Main supplies the complete enum labels; unique #71 changes and date-corrected output remain.

## Acceptance tails

From `/var/tmp/nl-pr-sync` (`sync/studio-ready`):

```text
$ python3 -m unittest discover -s tests
Ran 862 tests in 1829.519s
OK (skipped=4)

$ python3 -m unittest discover -s tests -p 'test_studio*.py'
Ran 101 tests in 592.536s
OK (skipped=1)
```

From `/var/tmp/nl-pr-sync-71` (`sync/f4-deploy-red`):

```text
$ python3 -m unittest discover -s tests
Ran 853 tests in 1966.141s
OK (skipped=4)
```

The #71 standalone Studio result will be added after it finishes.

Both full-suite runs emitted Python `ResourceWarning` messages for unclosed SQLite connections in test server cleanup. Their final unittest status is still `OK`; the warnings are recorded here and were not suppressed.
