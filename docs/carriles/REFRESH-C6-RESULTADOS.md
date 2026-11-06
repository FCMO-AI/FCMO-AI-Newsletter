# nl-refresh-c6 — verificación local

Ya existe: no aplica (arreglo y prueba de código propio); MEJORAR, R0 para el ajuste del oráculo y R2 para el guard existente que ejecuta pruebas en sandbox sin secretos. No se adoptan componentes ni dependencias.

## Causa y arreglo

El registro público `FCMO-303DC579C475` trae el tema científico `membership-inference`. Las tarjetas lo incluyen en `data-d-topics`; C6 buscaba la subcadena `membership` en todo el HTML y sólo exceptuaba la variante con espacio. El candidato reconstruido produjo exactamente 18 falsos positivos en archivo, edición, desk, organización y temas de EN/ES/ZH. La aserción fue `product-split strings still in built HTML (18 hits, first 25)` en `test_c6_no_split_product_strings`.

Extracto de la aserción reproducida antes del arreglo:

```text
FAIL: test_c6_no_split_product_strings
AssertionError: ... product-split strings still in built HTML (18 hits, first 25):
archive/index.html: 'membership'
beat/society/index.html: 'membership'
edition/2026-11-05/index.html: 'membership'
```

Se permite únicamente la variante con guion del mismo término científico. No se modifica el generador ni se elimina ninguna aserción previa. La regresión comprueba una tarjeta con su atributo y enlace reales, y sigue rechazando `membership plan`, la marca retirada y el formato personal retirado aunque compartan página con el término científico.

El diagnóstico tenía otra causa: unittest imprime la primera línea del docstring entre el nombre de la prueba y el separador del traceback. El parser requería que esas dos líneas fueran contiguas, por lo que perdía la aserción de C6. Ahora admite esa descripción y publica nombre, excepción y dos frames como máximo, conservando línea y función. Se omiten las rutas y líneas de código; siguen activos los filtros de privacidad, el límite de detalle y el escape de anotaciones y resumen.

El log entregado con el brief contenía rutas absolutas del runner que disparaban `NO_MACHINE_PATHS`. Se sustituyó sólo el prefijo del runner por `[runner]`; se conservan todo el texto diagnóstico y las marcas temporales originales.

## COMMITS

- `a364fe80d` — Allow the membership-inference research topic in C6.
- `c183f1a4b` — Preserve documented unittest failures in refresh diagnostics.
- El commit documental final contiene este informe, el log saneado y la nota de continuación.

## FINDINGS CLOSED

- nl-refresh-c6 / falso positivo: `test_c6_membership_inference_topic_is_research_not_a_product` falló con el scanner original y pasó con la excepción exacta.
- nl-refresh-c6 / diagnóstico: `test_documented_unittest_failure_keeps_identity_assertion_and_traceback` falló con el parser original y pasó con el arreglo, usando un subprocess unittest real y comprobando anotación y resumen.
- Evidencia del brief: `NO_MACHINE_PATHS` identificó exclusivamente el log del carril antes del saneamiento.

## FINDINGS NOT CLOSED

Los dos defectos pedidos quedan cerrados localmente. Los dos fallos de navegador heredados de la base siguen abiertos por la ausencia de Playwright, con identidad y aserción listadas abajo. La actualización pública no se ejecuta desde este carril; no se afirma que la edición viva haya avanzado. La deuda preexistente del límite del resumen de Actions queda registrada al final de `NEEDS.md`.

## ACCEPTANCE

| Comando / batería | Resultado |
| --- | --- |
| C6 sobre el candidato reconstruido, antes del arreglo | FAIL: 8 pruebas, 1 fallo; aserción exacta de 18 falsos positivos. |
| Las dos regresiones nuevas, con la implementación anterior | FAIL observado en ambas antes de corregir sus causas. |
| `python3 -m unittest tests.test_c6_one_fcmo tests.test_refresh_guard -v` | PASS: 27 pruebas, 138.993 s, código 0. |
| `python3 tools/refresh_guard.py --tests`, candidato reconstruido | PASS: código 0, 0 errores y 51 avisos de etiquetas no bloqueantes; sin omitir módulos. |
| Rebuild offline, schema, recibo, oráculo de traducción y `python3 tools/verify_release.py` | PASS: todos los comandos terminaron con código 0; 7 compuertas de release aprobadas. |
| Parser corregido contra el stderr real del candidato fallido | PASS: conserva identidad, aserción, traceback saneado y escapes de Actions. |
| `nice -n 10 ionice -c3 python3 -m unittest discover -s tests`, base exacta | FAIL heredado: 1379 pruebas en 4878.758 s; 2 fallos, 17 saltos, código 1. |
| Mismo comando, carril corregido | FAIL heredado: 1381 pruebas en 4869.650 s; los mismos 2 fallos, 17 saltos, código 1. **0 fallos nuevos**; las 2 pruebas añadidas pasan. |
| `git diff --check` y `NO_MACHINE_PATHS`, documentación final incluida | PASS: diff sin errores; 9791 archivos rastreados comprobados. |

Los únicos fallos de ambas suites tienen idéntica identidad y aserción por ausencia de Playwright:

- `test_d_band_collapse.BandCollapseTests.test_bone_bands_never_collapse_to_hairline_columns`: `AssertionError: None is not true : BROWSER_UNAVAILABLE: set PLAYWRIGHT_MODULE to the installed Node Playwright module path`.
- `test_d_word_space.DisplayWordSpace.test_rendered_space_never_collapses`: `AssertionError: BROWSER_UNAVAILABLE: set PLAYWRIGHT_MODULE to the installed Node Playwright module path`.

No se modificó ni se saltó ninguna de esas pruebas. La suite completa no se presenta como verde. Los 17 saltos son los que reporta unittest en cada árbol; no se añadieron saltos desde este carril.

La base de comparación es exactamente `origin/main@85fd777d9`, exportada a un repositorio temporal limpio con acceso de sólo lectura a los objetos Git locales. La suite posterior corre en `fix/refresh-c6-20261106`. Ambas usan temporales en disco mediante `TMPDIR`, sin omitir pruebas ni cambiar expectativas. Son árboles separados, por lo que aplicar el arreglo al carril no altera la base mientras ésta se ejecuta.

## Reproducción

Sin red ni credenciales. Se exportó `origin/main` a una copia temporal independiente y se utilizó su corpus saneado y su `site/data`. Se ejecutaron los pasos del workflow `daily-refresh.yml` en su mismo orden: ingest, sincronización de relaciones y locales, reconciliación, identidad, validación parcial, investigación, medios, superficies, pendientes, Story layer, schema, ACK, overlay, recibo, traducciones y verificación de release. Investigación y medios usaron sus opciones existentes `--offline`; no se reproducen las consultas externas de Actions. Story layer leyó la historia Git del worktree de este carril mediante `--history-git`.

El candidato contiene 903 historias vivas, 2 retiradas y 3 fusionadas; las 903 historias vivas tienen cobertura nativa completa EN/ES/ZH. El recibo contiene 6987 rutas. La copia recibió un índice Git propio y la historia completa para ejecutar las compuertas reales de archivos rastreados y ledger. Se descartaron los primeros intentos, que carecían de ese contexto o agotaron el volumen de temporales de 6 GB. Los resultados de aceptación usan temporales en disco. Los archivos generados permanecen sólo en la copia temporal y no se incorporan a estos commits.

Comandos ejecutados del workflow, en orden (sustituir `<worktree-del-carril>` por el repositorio local con historia completa):

```sh
python3 tools/ingest_corpus.py --corpus corpus --out release-src --i18n-dir site/data/i18n
python3 tools/synchronize_relationship_surfaces.py --site release-src
python3 tools/sync_airlocked_locales.py --corpus corpus --publication-src release-src
python3 tools/reconcile_locale_overlays.py --site release-src
python3 tools/refresh_locale_identity.py --site release-src
python3 tools/validate_localizations_partial.py --site release-src
python3 tools/public_research_desk.py --release-src release-src --offline
python3 tools/visual_desk.py --release-src release-src --site site --offline
python3 tools/build_newsroom_surfaces.py --release-src release-src --site site
python3 tools/mark_pending_localizations.py --site site --corpus corpus
python3 -m tools.story_layer build --corpus corpus --history-git <worktree-del-carril> --site site --i18n site/data/i18n --out site/data/stories.v2.json
python3 tests/harness/validate.py contracts/stories.v2.schema.json site/data/stories.v2.json
python3 tools/newsroom_receipt.py finalize --wire-status corpus/wire-status.json
python3 tools/build_final_release.py
python3 tools/build_ready_receipt.py
python3 tools/build_ready_receipt.py --check
python3 tests/oraculos/verificar_traduccion.py
python3 tools/verify_release.py
python3 tools/refresh_guard.py --tests
```

## UNVERIFIED

- El host avanzó `origin/main` durante las pruebas a `809be25a9`, con cambios de corpus y `PRODUCTION_STATUS.md`, sin modificar los archivos del arreglo. El corpus posterior no se reconstruyó ni se probó: la aceptación anterior está ligada al `85fd777d9` capturado al entrar.
- Actions y despliegue real: sin red, push ni promoción autorizados en este carril.
- Investigación y descubrimiento de medios por red: sustituidos por los modos offline existentes.
- Chromium/Playwright: Playwright no está instalado. No se equipara el guard local con la corrida de Actions que configura `FCMO_REQUIRE_BROWSER=1`.

## NEEDS.md

Sólo se añadió esta sección al final; las secciones anteriores se conservaron byte por byte:

```markdown
# nl-refresh-c6

## Resumen de Actions con más de 50 avisos (deuda preexistente)

El log y las anotaciones ya conservan nombre, aserción y traceback saneado. Hay otro límite en `tools/refresh_guard.py:render`: el resumen Markdown toma los primeros 50 hallazgos en orden de llegada. Con 51 avisos de etiquetas y un error posterior, el error aparece en el log/anotación pero queda fuera del resumen.

Reproducción sintética observada: `render(51 warnings + 1 error)` devuelve un error; la anotación contiene la aserción y el resumen no. Para una continuación del carril, priorizar los errores antes de limitar el resumen a 50 elementos y añadir una regresión con esa batería. Conservar todos los avisos en las anotaciones, su escape y los filtros de privacidad. No cambia la compuerta ni bloquea el diagnóstico por log solicitado en este brief.

## Avisos SQLite de la suite completa (fuera del arreglo del refresh)

Ambas corridas, base y carril, emiten `ResourceWarning: unclosed database` durante las pruebas de Studio/traducción. El punto de emisión de la recolección no identifica dónde se abrió la conexión; no se atribuye una causa sin esa evidencia. Continuación: reproducir esas pruebas con trazado de asignaciones, identificar al propietario de cada conexión y cerrarla en su salida/cleanup correspondiente, sin silenciar el aviso. Los avisos no se contaron como fallos ni se eliminaron del resultado.

El cierre de ambas suites también avisa de un socket de fixture sin cerrar; aplica la misma investigación de propietario/cleanup, sin suponer que el punto de recolección es la apertura.

## Navegador y base de comparación

La suite completa termina con los mismos dos fallos de navegador que la base: `test_d_band_collapse.BandCollapseTests.test_bone_bands_never_collapse_to_hairline_columns` y `test_d_word_space.DisplayWordSpace.test_rendered_space_never_collapses`, ambos `BROWSER_UNAVAILABLE`. Ejecutarlos en el host con Playwright disponible; no debilitar las aserciones ni instalar dependencias desde este carril.

La comparación se fijó a `origin/main@85fd777d9` al entrar. Durante su ejecución el host avanzó esa referencia a `809be25a9` (corpus y estado de producción; ningún archivo del arreglo). Ese corpus posterior no forma parte del candidato ni de la comparación ejecutada.
```

## KNOWN GAPS

- La base y el carril emiten avisos de conexiones SQLite sin cerrar durante las pruebas de Studio/traducción y de un socket de fixture al finalizar; quedaron anotados al final de `NEEDS.md`, sin atribuir su origen al punto donde el recolector los imprime.
- El guard reconstruido pasa con avisos de etiquetas de valores nuevos del corpus; la política existente los clasifica como no bloqueantes. No se cambió su nivel ni se añadieron traducciones.
- El resumen Markdown puede omitir un error después de 50 avisos, aunque el log y la anotación lo conservan; véase `NEEDS.md`.
- La verificación de producción, la adquisición por red y el navegador estricto permanecen fuera de la prueba local.

## CANON

- `standard/CORE.md` → L1: se corrigió la clasificación del término científico en el oráculo, sin ocultar datos ni dejar de escanear atributos. L5: se reconstruyó y comprobó el candidato nuevo; pasar C6 con el `site/data` anterior no se tomó como prueba de reparación del refresh ni de producción.
- `runtime/FCMO_RUNTIME_V1.txt` → se conservaron las fronteras observadas: corpus local, generación offline y ninguna afirmación de publicación o actualización viva.
- `AGENTS.md` (Hub) → el ruteo llevó al contrato local de Newsletter y su publicación fail-closed; no se aplicó el destino Claudex del encabezado genérico del brief.
- `disciplines/SOFTWARE_ENGINEERING.md` → se observaron ambas regresiones fallar antes de corregirlas y se ejercitaron el scanner sobre HTML y el diagnóstico sobre un unittest real.
- `ecosystem/repositories.json` → se identificó Newsletter como repositorio objetivo y se leyeron sus `AGENTS.md`, `AGENT_HUB.md` y estándar adaptado; no se editaron otros repositorios.
