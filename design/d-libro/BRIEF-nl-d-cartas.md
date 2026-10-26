# Brief carril nl-d-cartas (Luna) — D «Libro de evidencias» 1:1: cartas

Lee primero: `design/d-libro/CONTRATO.md` (manda), el Hub (`/srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt`,
`identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt`), `AGENTS.md` y `README.md` de este repo. Mira
R4-cartas, R4-carta y R4-movil-carta (y la sección LETTERS de R4-portada) en `/var/tmp/kyrion-test/c7/r4/`.

## Objetivo
Índice de cartas y página de carta (cartas de Javier y de Matías: Ghost vía `community.py` y pieces `fcmo-piece-v1` en
`editorial/pieces` vía `essays.py`/`essay_doc.py`, rutas `/cartas/<slug>/`) 1:1 con las referencias, en EN/ES/中文,
escritorio y móvil, generado desde datos. Autor, fecha, título, extracto e imagen sólo de los datos; si un campo falta, no se
inventa (nada de cargos tipo «Research editor»). 0 cartas = estado vacío honesto o la sección se oculta.
Además expón una función `render_letters_shelf(letters, locale_code) -> str` (tarjetas de la sección LETTERS de la portada,
markup y clases `.d-letter-card` en d-letters.css) para que el núcleo la llame.

## Dueño (exclusivo)
`tools/paper/{community,essays,essay_doc}.py`, `tools/paper/templates/essay.py`, `site-src/assets/css/essay.css`,
`site-src/assets/css/d/d-letters.css`, tests nuevos `tests/test_d_cartas*.py`. Usa las clases compartidas del contrato
(`.d-kicker`, `.d-section`, `.d-grade`…) tal cual; las implementa el carril nl-d-core en d-base.css: no las redefinas.
Si necesitas algo de build.py o layout.py, escríbelo en NEEDS.md (archivo, función, por qué) y no lo edites.

## Aceptación
- `python3 -m unittest discover -s tests` sin fallos nuevos frente a origin/main (conteos antes/después); tests
  `tests/test_d_cartas*.py` verdes con variantes: 0/1/n cartas, sin imagen, título largo, 中文, campos faltantes.
- Página de carta e índice renderizados desde fixtures; si puedes, capturas 1440/390 en `design/d-libro/capturas/cartas/`.
- `git diff --stat` dentro de tu lista de dueño. Reporte ≤10 líneas: COMMITS, FINDINGS, ACCEPTANCE, UNVERIFIED, CANON.

## Prohibido
Secretos, deploy, push, red, tocar archivos del otro carril, debilitar gates de privacidad/legal/i18n/publicación.
