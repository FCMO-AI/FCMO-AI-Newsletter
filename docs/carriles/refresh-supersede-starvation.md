# Carril nl-supersede: el refresh se descarta a sí mismo y la edición viva se congela

Lee primero el Agent Hub: /srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt y disciplines/SOFTWARE_ENGINEERING.md.
Ya existe: búsqueda en este repo (daily-refresh.yml, tools/corpus_guard.py release_lags_corpus) → ADAPTAR la transacción existente; no hace falta dependencia externa.

## Hecho medido (2026-11-06)
- De 2026-11-05 03:01 a 2026-11-06 12:36 UTC (33 h) ningún refresh llegó a main; la edición viva quedó en 2026-11-04.
- Cada corrida «exitosa» de `.github/workflows/daily-refresh.yml` imprimió
  «Refresh was superseded by newer product inputs; discard…» y salió 0 (ej. run 42198102424: empezó 09:50, commit 11:28).
- Causa: un rebuild tarda ~90 min; el bridge del newswire hace commit de `corpus/` cada hora. El paso
  «Commit only what the autonomous newsroom produced» descarta la build si `corpus` avanzó desde BUILD_BASE.
  Con duración > intervalo, toda build queda superada: inanición (livelock). La siguiente corrida tampoco gana.
- Un release más viejo que el corpus ya es un estado legítimo y tolerado (`tools/corpus_guard.py::release_lags_corpus`).

## Qué cambiar (archivos tuyos: `.github/workflows/daily-refresh.yml`, un script nuevo en `tools/` si lo extraes, y sus tests en `tests/`)
1. Un avance **sólo de `corpus/`** ya no descarta la build: se publica (rebase o reaplicación de las rutas generadas
   sobre origin/main), porque es estrictamente más nueva que lo vivo; el siguiente disparo reconstruye con el corpus nuevo.
2. Un avance de `scaffold/`, `tools/` o del workflow (constructor) **sí** descarta, como hoy.
3. **Monotonía:** nunca publicar encima de un release generado con corpus más nuevo que el propio. Compara
   `site/data/newsroom-status.json` (`airlock_generated_at` / `corpus_digest`) del candidato contra el de origin/main;
   si el remoto es más nuevo, descarta.
4. Si el rebase choca en rutas generadas (release-src, release-overlay, site, READY_TO_PUBLISH.md) y el candidato es
   más nuevo según (3), el candidato gana en esas rutas (se regeneran completas); fuera de esas rutas, conflicto = descartar.
5. Mensajes distintos para cada salida (publicado tras avance de corpus / descartado por constructor / descartado por
   release remoto más nuevo) para que la causa se vea en el log.
Extraer la lógica a `tools/refresh_promote.sh` (o .py) es preferible para poder probarla.

## Aceptación (corre y reporta cada una)
- Test nuevo con repos git temporales (bare remote + clon): (a) corpus avanzó → se publica y main contiene el release;
  (b) tools avanzó → descarta; (c) remoto con release más nuevo → descarta y no lo pisa; (d) conflicto en site con
  candidato más nuevo → publica el candidato; (e) nada avanzó → push normal. Rojo antes del cambio para (a) y (d).
- `python -m pytest -q tests/<tu test>` verde y la suite que toque el workflow/guard (`python -m pytest -q tests -k "refresh or corpus_guard"`) sin fallos nuevos.
- `python -c "import yaml;yaml.safe_load(open('.github/workflows/daily-refresh.yml'))"` y `actionlint` si existe.
- Commit en esta rama con mensaje claro. NO push, NO PR: Claude verifica fuera del sandbox y publica.
Prohibido: secretos, tocar otras rutas, force-push. Mantén tu contexto <80K. Reporte final ≤10 líneas con pass/fail.
