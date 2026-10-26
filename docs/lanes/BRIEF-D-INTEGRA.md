# Carril nl-d-integra — Newsletter D: suite verde con Cartas integrada

Contexto: Matías y Javier aprobaron R4 «Libro de evidencias» (10-26) para producción 1:1; contrato `design/d-libro/CONTRATO.md`. Esta rama une `c7/d-core-20261026` (núcleo D) y `c7/d-cartas-20261026` (Cartas). Lee `NEEDS.md` completo: ahí están los rojos, los oráculos C6 a migrar y los límites. Lee el Agent Hub (`runtime/FCMO_RUNTIME_V1.txt`, `disciplines/SOFTWARE_ENGINEERING.md`).

## Qué hacer
1. Integra `/cartas/` (o `/letters/`) y la portada en `tools/paper/build.py` como dejó pendiente nl-d-cartas; sin inventar contenido.
2. Corre la suite SERIAL (`python3 -m unittest discover -s tests`, nunca shards en paralelo; el host se quedó sin memoria hoy por eso) y arregla todo rojo atribuible a D o Cartas.
3. Migra SÓLO los tres oráculos C6 que NEEDS.md nombra (`test_v4_front_freshness`/`test_v4_front_plan`, `test_v4_mobile_first_viewport`, tipografía de `test_paper_build`), tal como NEEDS.md los especifica: misma fuerza de aserción contra el contrato D (filas, orden, ausencia de duplicados, destinos, archivos/subconjuntos y presupuesto). Ninguna otra prueba se debilita ni se borra. Por cada oráculo cambiado: antes→después en `docs/lanes/D-ORACULOS.md`.
4. Sanea las rutas de servidor de los dos briefs que marca `NO_MACHINE_PATHS` (no tocar la compuerta).
5. `design/build_css.py --check` (paper.css > 114688) falla también en main: no subas el límite; repórtalo.
Usa `TMPDIR=/var/tmp/nl-d-integra-tmp` para todo (no /tmp).

## Aceptación
- Suite completa serial: 0 fallos/0 errores nuevos frente a la base (base: 1270 OK, 9 omisiones). Pega la última línea.
- `python3 -m unittest tests.test_d_cartas tests.test_essay_template tests.test_essay_build` verde.
- `git diff --check` limpio.
Reporte ≤10 líneas: COMMITS, ACEPTACIÓN, ORÁCULOS (los 3), NO VERIFICADO, CANON.
Prohibido: push, red, secretos, tocar producción, borrar o debilitar pruebas fuera de esos tres oráculos.
