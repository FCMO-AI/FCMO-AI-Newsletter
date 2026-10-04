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
