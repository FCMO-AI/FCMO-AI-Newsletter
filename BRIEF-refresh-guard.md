# Newsletter: la edición viva está congelada en el 24-10 porque «Refresh the autonomous newsroom» falla en la guarda

Lee el Hub: `runtime/FCMO_RUNTIME_V1.txt`, `standard/CORE.md`, `disciplines/SOFTWARE_ENGINEERING.md`. Lee el `AGENTS.md` del repo.

**Hechos (GitHub, 10-26):**
- El newswire ya entrega: `corpus/wire-status.json` da transport OK, 705 registros, historias nuevas a las 09:29Z y 10:51Z (commits «corpus: receive verified FCMO newswire airlock»).
- El workflow `daily-refresh.yml` («Refresh the autonomous newsroom from the sanitized corpus») falló a las 09:29, a las 09:47 y en la corrida 40302262230. Paso «Guard the candidate against data that would break Deploy», `tools/refresh_guard.py --tests`: «refresh guard: 7 error(s)». Fallan test_gates, test_studio_integration, test_studio_live, test_v4_corpus_freshness, test_v4_front_freshness, test_v4_front_plan y test_story_layer. El log de Actions no trae el detalle.
- Por eso no hay edición nueva, Deploy sale «skipped» y la portada muestra «edición retrasada» (DELAYED / TRANSPORT_FAIL heredado).

**Objetivo:**
1. Reproduce localmente sobre este worktree (origin/main = be56f3167, que ya trae el corpus nuevo): corre los pasos del workflow `daily-refresh.yml` desde «ingest_corpus» hasta la guarda, en el mismo orden, generando el candidato. Luego `python tools/refresh_guard.py --tests`. Captura el detalle de los 7 errores.
2. Encuentra la causa raíz de cada uno. Hipótesis a descartar con evidencia: un registro nuevo del corpus que rompe un contrato (campo vacío, fecha o locale); el cambio de PR #139 (newswire aísla ediciones contaminadas); pruebas que fijan datos de una fecha concreta.
3. Arregla la causa en las herramientas de la redacción (`tools/`), no en los datos del corpus ni debilitando pruebas. Si una prueba fija un dato que legítimamente cambió (una fecha), corrígela para que siga comprobando la intención, y explícalo en el commit.
4. Añade una regresión con el registro problemático (o uno mínimo equivalente) que falle sin el arreglo.

**Owns:** `tools/`, `tests/`, `.github/workflows/daily-refresh.yml` sólo si la causa está ahí. No toques `corpus/`, `site/` generado ni `design/`.

**Aceptación** (comandos literales en el reporte):
- La reproducción del refresh y `python tools/refresh_guard.py --tests` dan 0 errores.
- La suite completa (`python -m unittest discover -s tests` o el comando que use el repo en CI) no tiene fallos nuevos frente a origin/main.
- Reporte en ≤12 líneas: los 7 errores con su causa (una línea cada uno), los commits, la regresión, lo UNVERIFIED y el bloque `CANON:` con rutas relativas.

Sin red, sin push y sin tocar GitHub: el integrador abre el PR.
