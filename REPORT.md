# L31 — CI de PR #61 y edición diaria
Fecha: 2026-10-07. Rama: `c5/l29-main`.

**Resultado: reparación local probada; PR todavía NO lista para merge.** El push no pudo autenticarse. GitHub sigue evaluando el commit anterior, con tres checks rojos y uno verde. La edición pública sigue siendo la del 2026-10-05; el correo diario está desactivado por su condición de ejecución.

## 1. CI observado en GitHub

PR: https://github.com/FCMO-AI/FCMO-AI-Newsletter/pull/61

| Check | Última corrida observada | Resultado |
| --- | --- | --- |
| test | https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37559891772 | failure |
| publish-gate | https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37559891837 | failure |
| release-integrity | https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37559891858 | failure |
| visual | https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37559891798 | success |

Los tres comandos requeridos `gh run view <id> --log-failed` se intentaron, pero la CLI carece de sesión autenticada. Los logs completos de los jobs se obtuvieron por el conector GitHub disponible.

- `publish-gate` y `release-integrity`: 817 pruebas; dos errores en los contratos de instalación/rollback de Studio. Simulaban systemd y el directorio personal, pero consultaban el usuario real del runner. El instalador rechazaba correctamente una cuenta distinta de `fcmo-agent`.
- `test`: 814 pruebas; diez errores y un fallo. Además de los dos errores del instalador, faltaban `age-keygen` y PyYAML. La prueba de Studio con remoto bare no podía obtener `origin/main` desde la fuente superficial; la integración HTTP también terminaba con el candidato rechazado. Este workflow no instalaba las dependencias de regresión ni traía el historial completo, a diferencia de los otros dos.

Corrección: las pruebas del instalador simulan también la cuenta del host. Una prueba adicional demuestra que `runner` y `root` siguen siendo rechazados antes de comandos o escrituras. El instalador de producción no cambió. El job `test` obtiene historial completo, desactiva la persistencia de credenciales e instala PyYAML 6.0.2 y age. No se omitió ningún check ni se debilitó una compuerta.

## 2. ¿Sale la edición diaria?

Al cierre de la consulta había **8 corridas**, no las 5 del brief: todas `skipped`; 6 por `workflow_run` y 2 programadas. Las dos programadas también omiten el único job sin ejecutar pasos:

- https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37671591246 — 2026-10-07 19:03:31 UTC.
- https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37674892371 — 2026-10-07 19:29:39 UTC.

En main, `dispatch-email.yml` exige `vars.FCMO_EMAIL_ENABLED == 'true'`. Para el evento programado, la otra parte de la condición se cumple automáticamente. Por tanto, **esa variable no vale literalmente `true` en las corridas observadas**. No se leyó su valor exacto ni se consultaron secretos o suscriptores. Se observaron 0 jobs de envío ejecutados. No existe otra ruta automática de Diario en los workflows examinados; una eventual actividad externa del proveedor no está verificada. No se activaron envíos.

La publicación web es otra ruta. Hubo despliegues exitosos el 2026-10-07, incluido:
https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37659087375

Sin embargo, la edición servida sigue siendo **2026-10-05**, con **46 historias vivas** y última finalización **2026-10-06 03:00:49 UTC**. Las rutas de edición del 2026-10-06 y del 2026-10-07 devuelven 404. Chromium renderizó la portada real con `DELAYED`; `status.json` conserva `FRESH`. Se verificó un viewport de 1440×900 sin overflow horizontal; esto no certifica ausencia de todos los defectos visuales.

El refresco del 2026-10-07 construye **48 historias**, pero el ACK rechaza el estado de traducciones porque todavía cuenta **46**:
https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37652020883

El ledger público tiene **80 registros**; sus tres entradas más recientes del 2026-10-07 reportan el mismo bloqueo 48/46. Esto coincide con los logs y el sitio.

**Causa y reparación:** se había eliminado del refresco la ejecución de `tools/mark_pending_localizations.py`, que genera `translation-status.json` desde las historias recién construidas. Se restauró ese paso después de construir las superficies y antes del ACK. Se conserva el rechazo de recibos incoherentes y la clasificación real de traducciones completas, pendientes o fallidas.

## 3. Evidencia local

Commits, con autor Codex:
- `13634b0`: regresiones rojas; 3 fallos reproducidos antes de corregir.
- `dd1c5d1`: corrección de CI y regeneración del recibo diario.

Verificación:
- `python3 -m compileall -q tools tests` y `git diff --check`: OK.
- Pruebas focalizadas: **11 OK**.
- `python3 ops/publish.py --check`: **821 pruebas OK, 1 omisión preexistente**, integridad **7/7**, compuertas **14/14**, navegador **3 idiomas × 2 viewports**, **138 rutas de noticias**.
- Repetición aislada con **106 archivos del corpus público reciente**, comprobados contra los hashes Git de la instantánea pública. Antes del paso restaurado, el ACK falla por el conteo viejo. Después: **50 historias**, **0 traducciones pendientes**, edición **2026-10-07**, ACK exitoso y **14/14** compuertas. El conteo 50 frente al 48 de main responde a la adaptación de etiquetas ya incluida en L30; L31 no cambió esa taxonomía.
- Navegador del candidato actualizado: **150 rutas de noticias**, **3 portadas**, **206 rutas chinas**, **2 viewports**; matrix **3×2 PASS**.

La repetición aislada usa investigación y visuales en modo offline; prueba la construcción y el ACK con bytes públicos reales, no un envío, deploy o ciclo autónomo de producción. Los archivos de publicación y el ledger del worktree no se actualizaron con esa instantánea.

Evidencia conservada, excluida de Git: `_audit/l31/red.log`, `focused.log`, `publish-check.log`, `replay-refresh.log`, `refreshed-browser.log`, `live-playwright.log`, `live-desktop.png`. Repetición: `_audit/l31/replay-refresh.py`. El oráculo de producción basado en Chrome CLI agotó su timeout; la observación DOM y captura indicadas se obtuvieron con Playwright.

## 4. Límite y continuación

El intento de push fast-forward a `c5/l29-main` falló: Git no pudo obtener usuario/credencial con los prompts desactivados. No se modificaron main, origin/main, otros worktrees, variables ni secretos. El head remoto sigue en `7f591ca`; la PR continúa en borrador y con CI inestable.

La carpeta de informes de campaña solicitada no está disponible para escritura en este entorno: crear `c5/reports` devuelve `Permission denied`. Se deja el mismo informe en `REPORT.md` y `reports/L31.md` dentro del worktree. El operador puede copiarlo al destino de campaña al recuperar esa ruta.

Para continuar, con la configuración gh autorizada:
1. Revalidar el head remoto y subir esta rama mediante push normal, sin force.
2. Confirmar los cuatro checks verdes para el nuevo head; una suite local verde no reemplaza ese resultado.
3. Claude debe repetir la aceptación fuera de este entorno antes de merge. El merge sigue siendo decisión del operador.
4. Tras merge, comprobar refresco → Pages → origen público y la edición recién servida. Observar ciclos posteriores para probar continuidad.
5. El correo requiere terminar la configuración autorizada del proveedor y sus requisitos existentes antes de activar `FCMO_EMAIL_ENABLED`; no basta con poner la variable en true.

**Resumen:** CI y refresco diario corregidos y probados localmente. La edición nueva todavía no está en producción, el correo no se ejecuta y la PR necesita push autenticado, CI verde y revisión.

# L33 — Drift del generador en el corte diario
Fecha: 2026-10-07. Rama: `c5/l29-main`.

## Causa

El check no depende del reloj. `verificar_generador_newsroom.py` genera desde `corpus/` y compara contra `release-src/`, además de conservar las pruebas sintéticas de crecimiento e idempotencia. La rama de la PR terminaba en el corpus del 6 de octubre; el `origin/main` local usado por el merge de CI ya había recibido en `ce24511` el airlock público del 7 de octubre. Al reproducir la unión, el oráculo falló en rojo: faltaban `data/editions/2026-10-07.json` y `editions/2026-10-07.html`, y divergían superficies derivadas. En la rama sin ese corpus actualizado, el mismo test pasaba, como lo había hecho antes en el host.

Por tanto, el release comprometido debe seguir al corpus vigente. El fallo señalaba drift real en el árbol combinado de la PR, no una fecha del runner que debiera fijarse o ignorarse.

## Corrección

Se incorporó a esta rama la actualización pública y sanitizada del corpus de `ce24511` (sello, índices y edición 2026-10-07); no se movió ni modificó la ref `origin/main`. Se reconstruyó `release-src` con `ingest_corpus.py` y `synchronize_relationship_surfaces.py`, más las etapas locales de sincronización/validación de locales y construcción de newsroom. `verificar_generador_newsroom.py` ahora pasa sin cambiar ni reducir sus invariantes de derivación, cobertura, crecimiento o punto fijo.

La investigación pública y la visual desk se ejecutaron en modo offline durante la reproducción; sus resultados derivados temporales y el `site/` temporal se descartaron, pues no podían sustituir una corrida de producción con acceso a fuentes. Luego se generaron con los constructores propios el overlay congelado y `READY_TO_PUBLISH.md`, que también estaban obsoletos frente a la nueva edición. No se afirmó publicación ni despliegue.

## Verificación

- Antes del arreglo, el oráculo específico falló sobre una copia desechable con el corpus de `origin/main`; después, `python3 -m unittest tests.test_refresco_diario.RefrescoDiario.test_generador_deriva_y_crece` pasó.
- `python3 tools/build_final_release.py`, `python3 tools/build_ready_receipt.py` y `python3 tools/verify_release.py`: PASS, 7/7 gates.
- `ops/publish.py --check`: PASS; suite completa, integridad, 14/14 gates y browser oracle PASS. La suite reportó 818 tests OK y 2 skips. El browser comprobó las superficies Story/portada chinas en 2 viewports y la matriz en 3 idiomas × 2 viewports.
- Los paths Playwright y `venv-pw` exactos dados en el brief no existen en este host. Primero se intentó el comando con esos valores. Para completar la aceptación de navegador se usó el módulo y Chromium ya instalados en `_audit/l31`; el PATH solicitado quedó antepuesto, aunque su directorio no está presente. Esta sustitución está documentada para la repetición de Claude.
- `git diff --check`: PASS. No se ejecutó `--publish`, no se hizo push y no se verificó producción en vivo.

## Límite

La verificación completa demuestra consistencia del árbol local y su candidato estático, no un deploy ni frescura del origen público. Claude debe repetir la suite desde un entorno con los paths de navegador acordados antes de merge; el arquitecto conserva la decisión de push.

**Resumen:** La CI fallaba porque `main` ya había avanzado el corpus al 7 de octubre y el release de la PR seguía en el 6. Se regeneraron el release, el overlay y el recibo; la aceptación local completa pasó con el navegador disponible en el worktree.

# L35 — PR #61 source-only merge against moving main
Fecha: 2026-10-07. Rama: `c5/l29-main`.

## Actualización frente al informe L33

L33 describe el estado anterior de esta rama y su regeneración de `release-src/`.
Para L35 integré el `origin/main` vigente (`d923f86`) y dejé los artefactos de
publicación exactamente como llegan de ese `main`. No regeneré corpus, release,
overlay, recibos, índices, paquetes de idioma ni ledger para perseguir el siguiente
refresh. El test de generador ya no usa ninguno de esos archivos como baseline.

## Cambio causal

En el merge de `main` con el corpus del 7 de octubre, el oráculo anterior falló en
rojo al comparar el corpus actual con `release-src/` todavía no compuesto: faltaban
cuatro dossiers y la edición del 7 de octubre, y diferían los índices derivados.
La regresión nueva también falló en rojo al ejecutar el oráculo sin `release-src/`
(`falta release-src`).

Ahora el adaptador crea una copia temporal del checkout, sustituye el corpus de
fixture por el `corpus/` actual y genera un `release-src/` de baseline dentro de esa
copia en cada ejecución. El oráculo heredado conserva las pruebas de punto fijo,
crecimiento de historia en todas las superficies, preservación de historias
anteriores y crecimiento de la siguiente edición; la fecha de esa edición se deriva
de la edición más nueva del corpus. La prueba de localización mide el paquete contra
la edición compuesta y verifica que todo delta ya importado es canonical y coincide
con su fuente, sin exigir que la salida generada preceda al escritor de corpus.
La justificación está en [CR-2026-10-07-generator-oracle-merge-drift.md](CR-2026-10-07-generator-oracle-merge-drift.md).

## Evidencia

- Suite completa en el árbol de código final antes del último heartbeat de `main`:
  **819 tests, 0 fallos, 2 omitidos**. El último commit de `main` incorporado (`d923f86`)
  solo cambió `corpus/wire-status.json`; tras integrarlo, los 34 tests de wire-liveness,
  refresco diario, aislamiento del generador y preservación de locales pasaron.
- `ops/publish.py --check` se ejecutó con Playwright 1.63.0 y Chromium 1243. Su suite
  interna pasó (**819 tests, 0 fallos, 2 omitidos**), pero el comando terminó rechazado
  antes del navegador. `verify_release.py` encontró artefactos heredados incoherentes
  en `origin/main`: overlay/manifest y recibo no coinciden con sus fuentes, y la
  localización congelada tiene campos sobrantes respecto del release. No los regeneré
  porque el encargo exige conservar esos artefactos de `main` sin cambios.
- Para separar esa falla del navegador, construí el candidato estático de `site/`
  fuera de los paths versionados, ejecuté las 14 compuertas (14/14), agent hygiene y
  `tests/oraculos/verificar_paper.py`: **PASS**, layout de 138 rutas de historia y
  3 portadas en dos tamaños, más la matriz de 3 idiomas × 2 tamaños.
- `corpus/`, `release-src/`, `release-overlay/final/`, `site/data/`, `site/assets/story-media/`,
  `READY_TO_PUBLISH.md`, `PRODUCTION_STATUS.md` y `ops/publication-desk/LEDGER.jsonl`
  son byte-a-byte iguales a `origin/main` en el diff final.
- Commits de esta ejecución: `0063c58` (merge de main), `a907002` (regresión roja),
  `c29a9ca` (oráculo dinámico), `f223f0c` (artefactos de locale desde main),
  `9c76b09` (locale contra release compuesto), `cedc68a` (retirar media no compuesta),
  `c4bc5ee` (heartbeat más reciente de main). Autor: `Codex <noreply@openai.com>`.

## Diff final y límite

Base: `origin/main` `d923f86`; HEAD antes de este reporte: `c4bc5ee`. El diff conserva
las fuentes de L29/L31 en `.github/`, `community/`, `contracts/`, `docs/`, `editorial/`,
`i18n/`, `legal/`, `ops/`, `site-src/`, `studio/`, `tests/` y `tools/`, además de los
reportes y documentos de seguimiento de esas lanes. En esta ejecución, los archivos
causales añadidos o modificados son:

- `tests/oraculos/verificar_generador_newsroom.py`
- `tests/oraculos/verificar_generador.py`
- `tests/test_generator_oracle_isolation.py`
- `tests/test_localization_completeness.py`
- `CR-2026-10-07-generator-oracle-merge-drift.md`
- `REPORT.md`

No hice push ni toqué la rama `main`. El objetivo `ops/publish.py --check` no queda
completado: la fuente de bloqueo son artefactos ya incoherentes en `origin/main`, y
resolverlo requiere regenerar la publicación o reparar su sincronización nativa;
ambas acciones quedarían fuera de la regla de conservar los artefactos de `main`.
Claude debe repetir el chequeo antes de merge. La rama sí deja la regresión de deriva
imposible por diseño y el candidato de navegador pasó de forma independiente.

**Resumen:** El oráculo ya prueba crecimiento desde un baseline generado en el mismo checkout y la suite pasa. `ops/publish.py --check` sigue bloqueado por release, recibo y locales incoherentes que ya trae `main`; no los alteré.

# L38 — corrección de coherencia del release

Fecha: 2026-10-07. Rama: `c5/l29-main`, PR #61.

Se corrigieron la vinculación de cada traducción con su inglés y la dependencia
del ACK de un recibo generado en un paso anterior. El diagnóstico, mecanismo y
regresiones están en [CR-L38.md](CR-L38.md).

Antes del cambio: `verify_release.py` reprodujo **4 de 7 compuertas fallidas**;
las dos regresiones iniciales fallaron y se comprometieron en `4d14d74` antes
de la corrección. Después de la recomposición: **7/7** compuertas, **50 historias**,
**0 parejas pendientes** y ACK de la entrega del 7 de octubre.

La prueba con una fuente modificada conserva la edición publicable con **49
historias nativamente completas y 1 pendiente** en cada locale. La ruta pendiente
no publica prosa traducida obsoleta y enlaza el inglés corregido.

Verificación final:

- `python3 -m unittest discover -s tests`: **824 pruebas OK, 4 omisiones**
  antes de añadir las dos últimas regresiones; estas pasan en el conjunto focalizado.
- Aceptación final: `PLAYWRIGHT_MODULE=$C/node-pw/node_modules/playwright PATH=$C/venv-pw/bin:$PATH python3 ops/publish.py --check --out /tmp/l38-check`:
  **exit 0**, **826 pruebas OK, 2 omisiones**, integridad **7/7**, compuertas **14/14**.
- Navegador: **150 rutas de noticias**, **3 portadas**, **206 rutas chinas**, dos
  tamaños; matriz **3 idiomas × 2 viewports PASS**. También se abrió y examinó
  la captura móvil de la portada española: sin overflow horizontal.
- Se usaron los paths de módulo y venv solicitados. Como el cache predeterminado
  de Playwright no tiene Chromium, se exportó `PLAYWRIGHT_BROWSERS_PATH` al cache
  ya disponible en `_audit/l31/browser-cache`. Playwright **1.63.0**, Chromium
  **153.0.8010.12**. La ejecución fue sin sandbox de filesystem; Chromium no fue
  rechazado y no se descargaron dependencias.
- `git diff --check`: PASS. El corpus no cambió. Los recibos de investigación
  conservados coinciden en firma con las fuentes; la Visual Desk fue offline.

Commits: `4d14d74` (regresión roja), `d2fe3e4` (mecanismo, contrato y release
coherente). Autor: `Codex <noreply@openai.com>`.

Logs y captura, excluidos de Git: `_audit/l38/red.log`, `drift-final.log`,
`unittest.log`, `publish-check.log`, `final-es-mobile.png`.

Push: se ejecutará el comando autorizado sobre `c5/l29-main` tras comprometer
este informe. No se ha afirmado despliegue; Claude debe repetir la aceptación
antes de merge y Pages debe confirmar después el origen público.

La ruta de campaña `STATE-AND-PLAN.md` y el log relativo de L35 indicado en el
brief no están disponibles en este entorno. Se leyeron el informe L35 de este
worktree, su CR, la doctrina requerida y las notas de localización del vault.
No se modificaron main, el corpus, otros worktrees ni el ledger del desk.

**Resumen:** mecanismo corregido, release coherente y aceptación completa en verde.
El resultado de subir la rama se registra a continuación; producción aún no verificada.
