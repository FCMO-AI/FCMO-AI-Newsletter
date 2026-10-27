# Carril: newswire bridge en rojo desde 2026-10-26 18:40Z (Newsletter, 2026-10-27)

Lee `AGENTS.md` de este repo y el Hub `runtime/FCMO_RUNTIME_V1.txt` + `disciplines/SOFTWARE_ENGINEERING.md` + `disciplines/HIGH_CONSEQUENCE.md` (/srv/fcmo/agents/repos/FCMO-Agent-Hub).

## Hechos (en `.scratch/`, no versionado)
- El workflow `Pull airlocked newswire with GitHub App` (`.github/workflows/newswire-bridge.yml`, copia en `.scratch/newswire-bridge.yml`) falla en cada corrida desde 10-26 18:40Z; último éxito 17:40Z. El Newsletter vivo muestra «edición retrasada» (`edition_state DELAYED`, `TRANSPORT_FAIL`).
- `.scratch/wire-status.json` (corrida 05:06Z): `transport_error: "VERIFY:PRIVATE_MARKER"` — el verificador estricto (`tools/newswire_bridge.py`, mensaje «private/implementation/strategic marker») encontró un marcador privado en el material de ARB.
- Corridas posteriores (`.scratch/run-40468486437.log`, 07:40Z) mueren antes, en «Select freshest sealed immutable ARB snapshot» con `step_exit=128` (git), y no actualizan wire-status.
- Árbol de ARB `origin/main` (sha en `.scratch/arb-origin-main.sha`) exportado en `.scratch/arb/` (sin .git). El CI de ARB no corre: GitHub Actions bloqueado por facturación (decisión humana, fuera de alcance).

## Objetivo
1. Causa raíz de cada falla, con evidencia local reproducible: corre el verificador estricto del bridge sobre `.scratch/arb` exactamente como lo hace el workflow y nombra QUÉ registro/campo/archivo dispara PRIVATE_MARKER (id del registro y patrón; nunca copies el texto privado en el reporte ni en commits). Para el 128: lee el paso y deduce qué comando git falla (p. ej. checkout del sha sellado, unshallow, sha ausente) y por qué empezó a fallar.
2. Arreglo en la capa correcta, sin debilitar NINGUNA guarda de privacidad/integridad:
   - Si el marcador es un falso positivo del patrón: afina el patrón con prueba que siga atrapando el caso real (no-regresión) y que deje pasar el caso nuevo.
   - Si es un marcador real en un registro de ARB: el bridge debe poner en cuarentena ESE registro (ya existe `tests/test_newswire_quarantine.py`: úsalo/extiéndelo) en vez de bloquear toda la edición, con recibo de por qué; o, si el contrato prohíbe cuarentena, documenta el cambio exacto que ARB debe hacer y prepara el parche ARB en `.scratch/arb-fix.patch`.
   - El 128: arreglo robusto (reintento acotado o selección correcta del snapshot sellado), con prueba.
3. Toda corrección trae una prueba que se pone roja si la falla vuelve.

## Aceptación (la corro fuera)
`python -m pytest -q tests/test_newswire_bridge.py tests/test_newswire_quarantine.py` y la suite completa de `tests/` sin fallos nuevos vs `origin/main` (mide la base primero); reproducción local documentada: comando que antes daba PRIVATE_MARKER sobre `.scratch/arb` y ahora pasa o pone en cuarentena con recibo. `git diff --check`.

## Prohibido
Red, push, `gh`, secretos, tocar `.scratch/arb` como fuente de verdad (es sólo lectura), debilitar aserciones o guardas, imprimir el contenido privado. Commits en español, `git -c user.name=fcmo-agent -c user.email=fcmo-agent@localhost`, trailer `Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>`.

## Reporte (≤10 líneas)
Causa de cada falla (registro/patrón por id), arreglo, conteos de pruebas, qué queda para ARB o para humanos. CANON con rutas completas.
