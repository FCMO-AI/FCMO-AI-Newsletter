# Carril nl-refresh-c6 · El refresh de la redacción falla en test_c6_one_fcmo (Codex Sol) · P1

Hecho: el workflow «Refresh the autonomous newsroom from the sanitized corpus» falló 3 veces seguidas el 2026-11-06 (01:55Z, 02:34Z, 03:49Z, run 42158815194). El paso «Guard the candidate against data that would break Deploy» dice sólo «test_c6_one_fcmo falló en el candidato», sin detalle (log en `docs/carriles/refresh-fail-42158815194.log`). Consecuencia: la edición viva se quedó en la del 11-04.

Lee: Hub `runtime/FCMO_RUNTIME_V1.txt`, `disciplines/SOFTWARE_ENGINEERING.md`; `AGENTS.md` del repo; `.github/workflows/` del refresh; `tests/test_refresh_guard.py`, `tests/refresh_guard_modules.txt`, `tests/test_c6_one_fcmo.py`.

Trabajo:
1. Reproduce: corre el refresh/guard en local sobre el corpus saneado (el mismo comando del workflow) y obtén la aserción exacta de test_c6_one_fcmo. Si no hay red para el corpus, usa el estado de `site/data` de main y la ruta del workflow que genere el candidato; dilo.
2. Causa en una línea con evidencia. Si es un dato legítimo nuevo (p. ej. un titular con «membership») que la prueba castiga por error, arregla la prueba o el generador en su capa; si es un defecto real del candidato, arregla el generador. Nunca debilites una aserción sin razón escrita.
3. El guard debe imprimir el detalle de la falla (nombre, aserción, primeras líneas del traceback) en el log de Actions: hoy no se puede diagnosticar desde CI.
4. Prueba de regresión que falle antes y pase después.

Aceptación: `python3 -m unittest tests.test_c6_one_fcmo tests.test_refresh_guard -v` verde; el guard sobre el candidato reproducido pasa; suite completa sin fallas nuevas respecto de origin/main (`nice -n 10 ionice -c3 python3 -m unittest discover -s tests`, cuenta antes/después). Commits pequeños en `fix/refresh-c6-20261106`. No hagas push ni toques main; lo fusiono yo.

Prohibido: secretos, `.env`, tocar otras ramas o worktrees (hay carriles de suscripción en curso en `nl-suscripcion-*`), workflows de deploy.
Devuelve ≤10 líneas: causa, arreglo, commits, aceptación pass/fail.
