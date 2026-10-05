# L1b-sync — resultado actual (2026-10-05)

Integración local de `origin/main` (`78197c4`) en `c5/v4` desde `a89c952`, con prueba roja previa `146bc93`. Se conserva WFSEC, se regeneran los artefactos con las herramientas del repositorio y se mantienen exactamente los datos y ediciones de main y la unión del ledger (63 líneas).

La suite final pasó: **595 pruebas, 0 fallos, 0 errores, 3 omisiones por navegador ausente**. `verify_release`: **7/7** (las seis originales y el gate de marca de main). Publicación: **13/13**, incluido `NO_FCMO_GROUP`. Se comprobaron **510 rutas y 27 817 enlaces locales**, con **0 roturas**, y las seis páginas EN/es-419/zh-Hans de las ediciones del 03 y 04 de octubre.

El detalle de conflictos, regeneración, conteos y reejecución está en [reports/L1b-sync.md](reports/L1b-sync.md). La prueba de conservación y rutas está en [reports/L1b-check.py](reports/L1b-check.py).

Dos registros nuevos se mantienen en cuarentena por `event_at: null`; los tombstones siguen vigentes. Falta el heartbeat real del bridge v4 (`WIRE_STATUS_MISSING`), así que el estado conserva `TRANSPORT_DOWN` / `DELAYED`. Las ediciones tienen rutas estáticas, sin inventar noticias aceptadas ni traducciones de su cuerpo histórico.

**Límite:** el arquitecto debe comprobar Playwright a 390 y 1440, volver a ejecutar las pruebas fuera de esta caja y realizar el push. No se verificó producción ni se usó red o secretos.

Resumen: merge local y gates verificados; faltan navegador en el host y el próximo ciclo real de publicación. Los informes que siguen son históricos.

---

# Campaign 5 — L1: integración y revalidación de v4

Fecha: 2026-10-04 UTC. Rama de trabajo: `c5/v4`.

## Resultado y límite

Se integró el `origin/main` disponible localmente mediante merge, conservando el historial de v4 y la unión exacta y cronológica del ledger. Se completó la localización de los nombres accesibles de navegación. La suite final ejecutó **561 tests, 0 fallas y 0 errores**; los 13 gates del periódico estático y las seis compuertas heredadas pasan.

No se verificó el navegador: esta caja no dispone de Playwright ni Chromium. El oráculo devuelve `BROWSER_UNAVAILABLE`; no se atribuyen mediciones de overflow, errores de consola ni aprobación visual. Claude debe repetir las verificaciones fuera de esta caja antes de integrar o publicar. No hubo fetch, push, deploy, acceso a secretos ni cambios en otras ramas o worktrees. La producción y su frescura siguen sin verificar en este carril.

## Integración

- Entrada v4: `ebad016b5dfc9c296ea1652ff28ce5f84eece111`.
- Entrada main: `d760a89cb924c78e552404aec244b01df5c82f3d`, referencia local que coincide con el plan de campaña; no se afirma haber consultado GitHub.
- Merge: `1e65db7`, padres `e2df24d` (pruebas rojas sobre v4) y `d760a89`.
- Divergencia original: 117 commits de v4 y 49 de main; estos últimos sólo añadían líneas al ledger.
- Ledger: v4 tenía 9 líneas, main 57, con 8 compartidas. Resultado: **58 líneas**, 58 run IDs distintos, ordenadas por `T0` convertido a UTC.
- Se comparó el multiconjunto de bytes de las líneas con `Counter(v4) | Counter(main)`: coincidencia exacta. No hubo saneamiento, reserialización ni pérdida de registros.
- SHA-256 final del ledger: `09bc5d189eaba32f1714d743972c9103d8dc11359e86a82365f83bcb8032f820`.
- `main` permanece en `75c3a80`, `origin/main` en `d760a89` e `integration/v4` en `ebad016`; sólo avanzó `c5/v4`.

## Pasada parcial recuperada

Se leyó el diff del worktree de integración anterior sin escribir en él. Se aplicaron sus cuatro archivos de código/catálogos: nombres accesibles localizados para las secciones, las migas y el pie de página. La prueba usa expectativas independientes para EN, es-419 y zh-Hans en portada técnica, archivo, historia y estado.

No se copió el apéndice de `CAMPAIGN-V4.md`: describe la interrupción y las pruebas de septiembre de otra activación, no evidencia de esta. Este informe conserva la decisión y las verificaciones nuevas. No se aplicaron cambios de diseño, CSS, contenido de noticias ni traducción de titulares; L6 conserva ese alcance.

## Fallos reproducidos y cambios causales

1. `e2df24d`: commit de pruebas previo al arreglo. La comprobación de nombres accesibles fallaba en 32 subcasos. El test de cronología ya pasaba en el ledger antiguo y pasa también tras el merge.
2. `4685e59`: aplica las etiquetas accesibles de los catálogos; los cinco tests de integración/ledger pasan.
3. La primera suite tras integrar ejecutó 559 tests: 0 fallas, **10 errores**, 2 skips. Los diez errores venían del mismo falso positivo de `NO_MACHINE_PATHS` en una línea nueva del ledger.
4. El registro `publication-desk-20260929T213717Z`, campo `reader_qa.visual`, dice `DOM/home/layout/editorial`. Es una secuencia relativa de nombres de comprobaciones, no una ruta absoluta. El diagnóstico inicial de ruta personal fue incorrecto y quedó corregido antes de editar el ledger.
5. `6f8e4d6`: segunda regresión roja; el texto relativo fallaba, mientras seis representaciones de una ruta absoluta seguían siendo rechazadas.
6. `a4f60b6`: el patrón del directorio personal exige un límite léxico izquierdo; conserva el rechazo de rutas absolutas en texto, asignaciones, JSON, HTML y URI de archivo. Los otros dos patrones permanecen equivalentes. No se exime el ledger ni ningún archivo adicional; no se desactiva ningún gate. Las 29 pruebas dirigidas pasan.
7. La comprobación del recibo detectó el cambio real de hash causado por las etiquetas. Se regeneró `READY_TO_PUBLISH.md` con su generador y se volvió a comprobar. No cambió el overlay congelado. Hash medido del candidato base: `f7abac14cdf7260d2b5ec2c83ef7e4adec123ba8b3ed57609909909ab2f2e656`.
8. `08a7be7`: conserva el prefiltro de bytes antes de evaluar el límite léxico, evitando aplicar la expresión regular a los archivos binarios que no contienen la firma. Las 24 pruebas de gates/límites y la suite completa vuelven a pasar. No se hizo una comparación controlada de rendimiento ni se atribuye una mejora de tiempo de la suite a este cambio.

## PR #49

Está disponible localmente como `origin/integration/paso1` en `d8d9db8`, y ya es antecesora de v4 y de esta rama. Sus cambios están incluidos; no se duplicaron con otro cherry-pick.

Se confirmaron `i18n/glossary.yml` y los tres avisos de `site/data/corrections.json`: retiro de `FCMO-FDBE3D996243` y fusiones de `FCMO-EEF757F0D806` y `FCMO-1E497EDC718A`. Los tres también existen en las correcciones del Story layer. La página estática actual renderiza los tipos genéricos de esos tres avisos; mejorar allí la explicación localizada es trabajo pendiente para L5, no prueba de que el lector ya reciba todo el aviso editorial.

## Verificación

- Baseline antes de cambios: **557 tests, 0 fallas, 0 errores, 2 skips**.
- Suite final sobre `08a7be7`: **561 tests, 0 fallas, 0 errores, 2 skips**, en **473.770 s**, salida 0. Incluye los oráculos de refresco completo; no se activó `FCMO_SKIP_STATEFUL_REFRESH_ORACLES`. Resultado en `_audit/c5-l1/final-suite.log`.
- `python3 -m compileall -q tools tests`: PASS.
- `git diff --check`: PASS.
- `python3 tools/verify_release.py`: **6/6 PASS**, incluido overlay/fuente, recibo, identidad/locales y rechazo de traducción falsa.
- Candidato moderno: **459 rutas**, 153 por locale, 123 rutas de historias vivas; construido de los artefactos comprometidos.
- Inspección del HTML final de esas 459 rutas: **1.374 nombres de navegación comprobados, 0 diferencias** frente a las etiquetas esperadas de cada idioma. Esto verifica el marcado accesible; no acredita rendering visual.
- `python3 tools/gates/run_all.py publish`: **13/13 PASS**, incluidos `NO_MACHINE_PATHS`, `AGENT_LAYER` y `NO_FCMO_GROUP`.
- Quedan **52 warnings** de glosario en prosa con origen ARB; el contrato existente los trata como advertencias. No se cambiaron las reglas ni esas traducciones.
- Navegador: **UNVERIFIED**. `resolve_playwright_module()` devuelve `None`; no se encontraron ejecutables Chromium/Chrome ni paquete Playwright instalado. No se descargó software por la restricción de red del brief.
- Los dos skips de la suite corresponden al harness de navegador y al oráculo móvil que requieren Playwright. Las pruebas con sockets sí se ejecutaron.

## Reproducción por Claude

Desde el checkout de la rama:

```sh
python3 -m compileall -q tools tests
python3 -m unittest discover -s tests -v
python3 tools/verify_release.py
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --out publish --base /FCMO-AI-Newsletter/
cp i18n/glossary.yml publish/data/glossary.json
python3 tools/gates/run_all.py publish
python3 tests/oraculos/verificar_paper.py publish
```

Para el último comando, proporcionar un módulo Playwright y Chromium ya instalados mediante `PLAYWRIGHT_MODULE` y la configuración normal del harness. Ejecutar EN/es-419/zh-Hans a 390×844 y 1440×900, comprobar `scrollWidth == clientWidth` y cero errores de consola, y revisar los frames como lector. Ampliar el barrido a las historias para L6. No presentar el PASS de HTML/gates como aprobación visual.

La prueba adicional de conservación exacta puede repetirse con estos commits inmutables:

```python
from collections import Counter
from pathlib import Path
import subprocess
path = "ops/publication-desk/LEDGER.jsonl"
def lines(ref):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"]).splitlines()
assert Counter(Path(path).read_bytes().splitlines()) == (
    Counter(lines("ebad016")) | Counter(lines("d760a89"))
)
```

Logs y prueba del ledger de esta caja quedan en `_audit/c5-l1/` (ignorados por Git). No se requieren para confiar en el informe: las órdenes anteriores son la prueba independiente. La integración externa, el push y la publicación siguen sujetos a la revisión de Claude y a D1; la aprobación visual corresponde a L6/D6.

Resumen: v4 integra el main local conservando las 58 líneas exactas del ledger; accesibilidad y gates están corregidos y verificados localmente. Falta la revisión real en navegador fuera de esta caja y la decisión de publicación del operador.

## L5-corr — correcciones localizadas

L5 completó la vista localizada del ledger y las rutas de aviso para los tres registros de corrección. La evidencia y el límite de producción están en [REPORT-L5-corr.md](REPORT-L5-corr.md). Commits de este carril: `e215994` (prueba roja) y `4e3c3fa` (arreglo y recibo medido).

Resumen: las tres correcciones aparecen con texto nativo y enlace útil en EN, es-419 y zh-Hans; suite y gates pasan localmente. Falta la comprobación de Claude fuera de esta caja y la inspección del sitio en producción.

## L10-ci — CI visual gate

The all-routes visual CI gate and pull-request workflow are committed locally. The candidate build passed all 13 release gates, including `NO_FCMO_GROUP`; the full Python suite passed with 563 tests, 0 failures/errors, and 3 skips.

The browser run could not be completed in this container because Playwright and Chromium are unavailable. The seeded overflow regression test is present and will execute on the architect's host when Chromium is installed. Detailed implementation, evidence, and host continuation commands are in [REPORT-L10-ci.md](REPORT-L10-ci.md).

Commits: `a463361` (red test first), `bd016cf` (implementation and lane report), plus this report update. No push was made.

Resumen L10: la puerta visual y sus pruebas están listas; falta ejecutarlas con Chromium en el host.

## L3-fresh — frescura independiente del heartbeat

Detalle, evidencia roja-primero y continuación en [REPORT-L3.md](REPORT-L3.md).
Resumen: frescura independiente del heartbeat, estado público FRESH / QUIET / DELAYED y diagnóstico conservado. Sin push; navegador y producción pendientes de verificación independiente.

## L16-mobile — primera pantalla y overflow zh-Hans

Detalle, baseline, cambios y continuación para la prueba del arquitecto en [REPORT-L16-mobile.md](REPORT-L16-mobile.md). La suite completa da 583 OK y 3 omitidas. El navegador no está disponible en esta caja, así que el resultado visual posterior sigue sin confirmación.

Resumen L16-mobile: navegación compacta y wrapping genérico implementados; falta medir el candidato en Chromium en el host.


## Imported main workflow security report (historical)

# Campaña 5 — WFSEC

La contención local de las salidas privadas está implementada y probada. El
backfill público está retirado. Los workflows restantes emiten únicamente códigos
de salida y conteos desde sus bloques shell.

**Aceptación pendiente:** `python3 -m unittest discover -s tests` ejecutó 72 tests:
70 pasan y 2 fallan por las referencias de Actions aún sin SHA cotejado. Se pidió
la excepción de red necesaria para consultar código y metadatos de GitHub; no hubo
respuesta ni acceso de red. No hubo push ni cambios en GitHub.

El commit rojo es `4e90763`, con autor `Codex <noreply@openai.com>`. La prueba final
también falla contra los tres workflows originales de `origin/main`: 28 fallos de
subcasos, 0 errores. Los cuatro tests independientes de los pins pasan con fixtures
de éxito, fallo, excepción y error de Git.

Detalles, límites, continuación y rangos conservadores de logs a retirar:
[REPORT-WFSEC.md](REPORT-WFSEC.md). Claude debe reejecutar antes de integrar.

Resumen: contención probada; faltan los SHA verificados. No integrar ni reactivar
hasta completar ese paso y obtener el suite entero en verde.

## L1c-hermetic — test de registro arrastrado

`TemporaryCorpusTests.test_carried_record_stays_live` now constructs its temporary corpus from fixtures only and calls the story layer without the live site or repository history. It continues to verify live/carry-forward status, preserved first-publication time, and empty stderr. The pre-change focused test failed on the two current null-date records and history alerts; after the change it passes.

Both `FCMO-045BB8282222` and `FCMO-5B5B447325A8` have `event_at: null`, no `published_at`, and only intake/verification timestamps plus first-edition date `2026-10-03`. Those fields do not establish the underlying event dates. They remain quarantined, and the one-line source-backed date/provenance request for ARB is in [reports/L1c-hermetic.md](reports/L1c-hermetic.md).

Verification on this worktree: `python3 -m unittest discover -s tests` — 595 tests OK, 3 skipped; `python3 tools/verify_release.py` — 7/7; fresh `tools/paper/build.py` candidate followed by `python3 tools/gates/run_all.py publish` — 13/13. The first gate attempt targeted a stale pre-existing `publish/` and failed on old routes; rebuilding the candidate cleared those mismatches. Browser rendering remains unverified because `PLAYWRIGHT_MODULE` is unavailable in this shell. Full lane evidence and continuation boundary: [L1c-hermetic report](reports/L1c-hermetic.md).

Resumen: el caso de arrastre quedó aislado con fixtures; suite y compuertas pasan. Ambas noticias esperan fechas de evento verificables de ARB.
