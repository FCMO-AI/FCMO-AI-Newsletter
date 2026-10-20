# Rendimiento del build del periódico

Referencia: `2c64eb8e4`. Corpus de entrada: 586 historias, 583 vivas,
2 745 páginas de temas/organizaciones y 4 695 rutas del renderer.
Los comandos consumieron los mismos archivos versionados de historias, estado,
editorial, gráficos e historial de citas. No se cambió contenido publicado.

## Resultado sin profiler

Python 3.13.5, `nice -n 15`, afinidad de CPU limitada a un máximo de dos núcleos
por proceso y salidas en almacenamiento temporal en memoria. El builder es
secuencial. Las otras verificaciones concurrentes
usaron CPU distintas; estos tiempos incluyen carga del host y no son un ensayo
microarquitectónico aislado.

| Comando | Antes (s) | Después (s) |
|---|---:|---:|
| `tools/paper/build.py` | 808.626 | 25.317 |
| `tools/validate_agent_hygiene.py` | 9.749 | 10.488 |
| `tools/gates/run_all.py` | 93.494 | 117.413 |
| Total | 911.870 | 153.218 |

El tramo completo queda por debajo de cinco minutos. Las catorce compuertas
pasan en ambos árboles. Higiene y compuertas no tienen cambios; la variación de
sus tiempos corresponde a ejecuciones distintas sobre bytes idénticos.

## Cambio causal y guardas

`PaperBuilder._topic_links` calculaba membresías recorriendo todas las historias
por cada valor de cada historia y por cada página. Con 3 899 membresías y
2 745 páginas, el trabajo anterior rondaba 6 240 millones de comprobaciones.
Ahora cuenta membresías una vez por build, conserva el orden de primera aparición
para empates, ordena una vez y sólo construye las URLs seleccionadas. El índice
pertenece a una instancia del builder; no hay caché global entre ediciones.

El perfil completo atribuye el 98,3 % del tiempo anterior a `_topic_links`:
1 881,816 s frente a 1,038 s después, con las mismas 2 745 llamadas y la misma
configuración de instrumentación.

`tests/test_paper_performance.py` añade tres pruebas sin reloj:

- `test_taxonomy_membership_is_counted_once_for_all_pages_and_locales`: con
  32 historias y 18 páginas, la base realiza 73 728 visitas frente a 96 nuevas;
  el límite generoso es cuatro recorridos del corpus.
- `test_only_selected_taxonomy_urls_are_rendered`: la base construye 50 URLs
  para mostrar cinco; el renderer corregido construye cinco.
- `test_membership_duplicates_ties_exclusions_and_limits_keep_exact_order`:
  conserva duplicados por historia, umbral de temas, separación de organizaciones,
  empates por mayúsculas, colisiones de slug, exclusión por nombre/slug,
  límites cero/positivos/negativos y aislamiento entre builders.

Se observaron fallar ambas guardas de complejidad contra el código original.
Las tres pruebas pasan con el cambio. También pasan las tres pruebas existentes
de `tests/test_studio_renderer_cache.py`.

`run_all.py` no contiene comprobaciones de navegador: ejecuta una vez cada una
de las catorce compuertas. Ya anuncia comienzo y duración por compuerta en la
base heredada. El oráculo de navegador pertenece al paso posterior de publicación;
esta optimización no cambia su cobertura ni sus límites.

## Identidad de salida

Los manifiestos SHA-256 de **16,860 archivos**, incluidos los binarios,
contienen los mismos nombres relativos y hashes. Tamaño total: **177,215,649 bytes**.
`diff -u before.sha256 after.sha256` y `diff -r before after` terminan con código
cero y salida vacía. Los builds completos usados para los perfiles también
reproducen ese manifiesto.

SHA-256 de ambos manifiestos:

`9a799a67d101c6e460fd600020a774c11530789561e9beec9c1bad6d49cee16b`

Cada línea del manifiesto contiene `SHA256`, dos espacios, la ruta relativa y
un salto de línea; los archivos se ordenan por ruta y se incluyen los ocultos.

## Perfiles completos

El build usa `cProfile.Profile.enable(subcalls=False, builtins=False)` para
reducir la sobrecarga de registrar miles de millones de llamadas. Higiene y
compuertas usan `python3 -m cProfile -o PROFILE ...`. Los tiempos siguientes son
con instrumentación y no se usan para el presupuesto de cinco minutos.
Una primera captura de build con todas las llamadas activadas se interrumpió a
los 658 s; no se presenta como un build terminado. El perfil completo con menor
sobrecarga sustituye esa captura.

| Paso perfilado | Antes (s) | Después (s) |
|---|---:|---:|
| build | 1914.206 | 38.212 |
| hygiene | 27.135 | 30.956 |
| gates | 202.560 | 252.685 |

### Build antes: 15 mayores tiempos acumulados

| Llamadas | Acumulado (s) | Función |
|---:|---:|---|
| 1 | 1914.159 | `tools/paper/build.py:1(<module>)` |
| 1 | 1914.036 | `tools/paper/build.py:932(main)` |
| 1 | 1913.841 | `tools/paper/build.py:803(build)` |
| 2,874 | 1890.918 | `tools/paper/build.py:595(_listing)` |
| 2,745 | 1881.816 | `tools/paper/build.py:285(_topic_links)` |
| 4,275,100,752 | 904.467 | `tools/paper/build.py:292(<genexpr>)` |
| 1,971,185,712 | 414.773 | `tools/paper/build.py:296(<genexpr>)` |
| 17,089,402 | 52.752 | `tools/paper/routes.py:84(slugify)` |
| 1,758 | 14.502 | `tools/paper/build.py:422(_story)` |
| 89,304 | 9.698 | `tools/paper/i18n.py:31(story_locale)` |
| 120,441 | 9.575 | `tools/paper/i18n.py:100(field)` |
| 1,749 | 7.718 | `tools/paper/build.py:237(_story_navigation)` |
| 6,443,082 | 6.736 | `tools/paper/routes.py:76(href)` |
| 15,096 | 6.208 | `tools/paper/build.py:598(<genexpr>)` |
| 21,429,513 | 6.095 | `tools/validate_localizations.py:267(prose_leaves)` |

### Build después: 15 mayores tiempos acumulados

| Llamadas | Acumulado (s) | Función |
|---:|---:|---|
| 1 | 38.209 | `tools/paper/build.py:1(<module>)` |
| 1 | 38.086 | `tools/paper/build.py:936(main)` |
| 1 | 37.964 | `tools/paper/build.py:807(build)` |
| 1,758 | 19.684 | `tools/paper/build.py:426(_story)` |
| 89,304 | 11.186 | `tools/paper/i18n.py:31(story_locale)` |
| 120,441 | 11.020 | `tools/paper/i18n.py:100(field)` |
| 1,749 | 10.147 | `tools/paper/build.py:237(_story_navigation)` |
| 2,874 | 10.024 | `tools/paper/build.py:599(_listing)` |
| 15,096 | 7.369 | `tools/paper/build.py:602(<genexpr>)` |
| 21,429,513 | 6.887 | `tools/validate_localizations.py:267(prose_leaves)` |
| 43,848 | 5.787 | `tools/paper/i18n.py:110(headline)` |
| 24,588 | 5.390 | `tools/paper/i18n.py:178(truncate)` |
| 1,749 | 4.556 | `tools/paper/build.py:219(_related_stories)` |
| 35,049 | 3.920 | `tools/paper/i18n.py:117(dek)` |
| 24,588 | 3.600 | `tools/paper/i18n.py:169(visual_width)` |

### Higiene antes: 15 mayores tiempos acumulados

| Llamadas | Acumulado (s) | Función |
|---:|---:|---|
| 27 | 27.069 | `~:0(<built-in method builtins.exec>)` |
| 1 | 27.069 | `tools/validate_agent_hygiene.py:1(<module>)` |
| 1 | 27.042 | `tools/validate_agent_hygiene.py:181(main)` |
| 1 | 27.036 | `tools/validate_agent_hygiene.py:86(validate)` |
| 7,770 | 25.915 | `tools/validate_agent_hygiene.py:53(_load_jsonld)` |
| 7,770 | 25.423 | `parser.py:123(feed)` |
| 7,770 | 25.416 | `parser.py:153(goahead)` |
| 1,172,766 | 13.808 | `parser.py:338(parse_starttag)` |
| 8,378,952 | 4.560 | `~:0(<method 'match' of 're.Pattern' objects>)` |
| 1,015,324 | 3.498 | `parser.py:416(parse_endtag)` |
| 1,172,766 | 2.187 | `parser.py:382(check_for_whole_start_tag)` |
| 4,401,081 | 1.821 | `_markupbase.py:44(updatepos)` |
| 3,795,867 | 1.059 | `~:0(<method 'group' of 're.Match' objects>)` |
| 1,553,630 | 0.965 | `parser.py:77(_unescape_attrvalue)` |
| 4,965,815 | 0.728 | `~:0(<method 'end' of 're.Match' objects>)` |

### Higiene después: 15 mayores tiempos acumulados

| Llamadas | Acumulado (s) | Función |
|---:|---:|---|
| 27 | 30.823 | `~:0(<built-in method builtins.exec>)` |
| 1 | 30.823 | `tools/validate_agent_hygiene.py:1(<module>)` |
| 1 | 30.795 | `tools/validate_agent_hygiene.py:181(main)` |
| 1 | 30.787 | `tools/validate_agent_hygiene.py:86(validate)` |
| 7,770 | 29.144 | `tools/validate_agent_hygiene.py:53(_load_jsonld)` |
| 7,770 | 28.559 | `parser.py:123(feed)` |
| 7,770 | 28.550 | `parser.py:153(goahead)` |
| 1,172,766 | 15.529 | `parser.py:338(parse_starttag)` |
| 8,378,952 | 5.055 | `~:0(<method 'match' of 're.Pattern' objects>)` |
| 1,015,324 | 3.973 | `parser.py:416(parse_endtag)` |
| 1,172,766 | 2.455 | `parser.py:382(check_for_whole_start_tag)` |
| 4,401,081 | 2.052 | `_markupbase.py:44(updatepos)` |
| 3,795,867 | 1.196 | `~:0(<method 'group' of 're.Match' objects>)` |
| 1,553,630 | 1.067 | `parser.py:77(_unescape_attrvalue)` |
| 4,965,815 | 0.818 | `~:0(<method 'end' of 're.Match' objects>)` |

### Compuertas antes: 15 mayores tiempos acumulados

| Llamadas | Acumulado (s) | Función |
|---:|---:|---|
| 54 | 202.504 | `~:0(<built-in method builtins.exec>)` |
| 1 | 202.504 | `tools/gates/run_all.py:1(<module>)` |
| 1 | 202.456 | `tools/gates/run_all.py:49(main)` |
| 1 | 202.455 | `tools/gates/run_all.py:36(run)` |
| 38,843 | 123.159 | `parser.py:123(feed)` |
| 38,843 | 123.110 | `parser.py:153(goahead)` |
| 5,174,575 | 71.311 | `parser.py:338(parse_starttag)` |
| 1 | 51.747 | `tools/gates/english_leak.py:116(check)` |
| 1 | 45.969 | `tools/gates/broken_reference.py:84(check)` |
| 6,778,647 | 28.875 | `~:0(<method 'search' of 're.Pattern' objects>)` |
| 1 | 28.677 | `tools/gates/remote_script.py:28(check)` |
| 1 | 25.502 | `tools/gates/internal_id.py:52(check)` |
| 37,184,573 | 20.344 | `~:0(<method 'match' of 're.Pattern' objects>)` |
| 1 | 17.750 | `tools/gates/personal_mailbox.py:21(check)` |
| 4,479,835 | 15.996 | `parser.py:416(parse_endtag)` |

### Compuertas después: 15 mayores tiempos acumulados

| Llamadas | Acumulado (s) | Función |
|---:|---:|---|
| 54 | 252.606 | `~:0(<built-in method builtins.exec>)` |
| 1 | 252.606 | `tools/gates/run_all.py:1(<module>)` |
| 1 | 252.549 | `tools/gates/run_all.py:49(main)` |
| 1 | 252.548 | `tools/gates/run_all.py:36(run)` |
| 38,843 | 159.289 | `parser.py:123(feed)` |
| 38,843 | 159.220 | `parser.py:153(goahead)` |
| 5,174,575 | 92.441 | `parser.py:338(parse_starttag)` |
| 1 | 63.822 | `tools/gates/broken_reference.py:84(check)` |
| 1 | 57.784 | `tools/gates/english_leak.py:116(check)` |
| 1 | 43.639 | `tools/gates/internal_id.py:52(check)` |
| 1 | 34.317 | `tools/gates/remote_script.py:28(check)` |
| 6,778,647 | 29.944 | `~:0(<method 'search' of 're.Pattern' objects>)` |
| 37,184,573 | 26.275 | `~:0(<method 'match' of 're.Pattern' objects>)` |
| 4,479,835 | 20.402 | `parser.py:416(parse_endtag)` |
| 92,331 | 16.246 | `_local.py:541(read_text)` |

## Aceptación de pruebas y límite heredado

`nice -n 15 python3 -m unittest tests.test_paper_performance tests.test_studio_renderer_cache -v`:
seis pruebas aprobadas con el renderer final. Ambas guardas de complejidad se
observaron fallar primero contra la base; no se cambió ninguna aserción existente.

`nice -n 15 python3 -m unittest discover -s tests -v`:

```text
FAIL: test_local_check_prepares_a_receipt_before_the_integrity_gate (test_ready_receipt_pipeline.ReadyReceiptPipelineTests.test_local_check_prepares_a_receipt_before_the_integrity_gate)
Ran 992 tests in 2389.264s
FAILED (failures=1, skipped=4)
```

La discovery empezó antes de añadir la tercera guarda de rendimiento; la
invocación enfocada posterior cubre las tres guardas finales y las tres pruebas
de caché de Studio. `test_studio_live.BareRemote` pasa completo, incluidos ensayo,
edición, revisiones y comprobaciones reales sobre el bare remoto local.

La suite no se acredita verde. El fixture
`ReadyReceiptPipelineTests.test_local_check_prepares_a_receipt_before_the_integrity_gate`
parchea `publish.subprocess.run`, mientras publicación usa `publish.run_command`
con `Popen`. Lanza otra discovery real y puede repetirse recursivamente. Se detuvo
solamente esa discovery hija; la suite exterior continuó y su fallo refleja esa
interrupción. Los archivos del fixture y del lanzador no tienen diferencias
respecto a la base del carril.

`NEEDS.md`, sección `paper-perf`, prescribe cambiar sólo el destino del mock a
`publish.run_command` conservando todas sus aserciones. Una copia en memoria con
esa única sustitución pasa en 0,006 s. Un probe con `Popen` interceptado antes de
crear hijos confirma que el fixture original intenta lanzar la suite completa.
El archivo fuera del alcance no se modificó.

Los skips observados fueron:

- setUpClass (harness.test_harness_tools.BrowserRunTests) ... skipped 'playwright not reachable through NODE_PATH'
- test_fixture_with_horizontal_overflow_fails_the_real_browser_oracle (test_ci_visual_gate.CiVisualGateTests.test_fixture_with_horizontal_overflow_fails_the_real_browser_oracle) ... skipped 'Playwright/Chromium is not installed'
- test_absent_renderer_fails_closed (test_studio_preview.PreviewIdentity.test_absent_renderer_fails_closed) ... skipped 'Renderer integration is present; exercised by byte-identity test.'
- test_the_real_build_passes_the_first_viewport_oracle (test_v4_mobile_first_viewport.OracleInBrowserTests.test_the_real_build_passes_the_first_viewport_oracle) ... skipped 'Playwright module does not resolve from this checkout'

No se ejecutó Chromium real ni se comprobó despliegue, producción o frescura del
origen público. El carril prohíbe red y push. Las pruebas de oráculos que usan
fixtures de navegador no acreditan un navegador real. Hubo avisos existentes de
SQLite por conexiones de test sin cerrar; no se suprimieron.

## Reproducción

Usar un directorio de salida distinto para cada revisión y las mismas entradas:

```sh
candidate=$(mktemp -d)
GHOST_CONTENT_URL='' GHOST_CONTENT_API_KEY='' nice -n 15 python3 tools/paper/build.py \
  --stories site/data/stories.v2.json --status site/data/newsroom-status.json \
  --editorial editorial --out "$candidate/site" --base /FCMO-AI-Newsletter/
nice -n 15 python3 tools/validate_agent_hygiene.py --site "$candidate/site"
nice -n 15 python3 tools/gates/run_all.py "$candidate/site"
```

Para perfilar el build con menor sobrecarga, conservar los mismos argumentos,
configurar `sys.argv` para `tools/paper/build.py` y envolver
`runpy.run_path('tools/paper/build.py', run_name='__main__')` así:

```python
import cProfile
import runpy

profiler = cProfile.Profile()
profiler.enable(subcalls=False, builtins=False)
try:
    runpy.run_path('tools/paper/build.py', run_name='__main__')
finally:
    profiler.disable()
    profiler.dump_stats('build.prof')
```

Ordenar los perfiles mediante `pstats.Stats('build.prof').sort_stats('cumulative').print_stats(15)`.
Para los otros dos comandos, anteponer `python3 -m cProfile -o PROFILE` a la ruta
del script y sus argumentos. Los tiempos ordinarios deben medirse por separado
con `time.monotonic()` alrededor del comando completo, sin profiler.
