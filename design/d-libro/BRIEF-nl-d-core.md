# Brief carril nl-d-core (Sol) — D «Libro de evidencias» 1:1: núcleo del sitio

Lee primero: `design/d-libro/CONTRATO.md` (manda), el Hub (`/srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt`,
`identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt`, `disciplines/VISUAL_ENGINEERING.md`), y en este repo
`AGENTS.md`, `README.md`, `design/CSS-CLASS-INVENTORY.md`. Abre y mira las referencias R4-portada, R4-historia, R4-archivo,
R4-metodo y R4-movil-portada en `/var/tmp/kyrion-test/c7/r4/`.

## Objetivo
El sitio generado por `tools/paper/build.py` se ve 1:1 como las referencias en portada (Today), página de historia, archivo,
método («How we work»/método y páginas institucionales simples: about, corrections, status, privacy, license…), búsqueda,
temas, nav y pie, en EN/ES/中文, escritorio y móvil, desde los datos reales y de forma automática (ver «Sistema» del contrato).

## Dueño (exclusivo)
`tools/paper/build.py`, `tools/paper/templates/{layout,landing,pages,reader,newsletter,subscribe,subscription_states}.py`,
nuevos `tools/paper/templates/d_*.py`, `site-src/assets/css/d/{d-base,d-front,d-story}.css`, `design/tokens.json`,
`design/build_css.py`, `site-src/assets/css/paper.css` (puedes retirarlo de las páginas que pases a D), tests nuevos
`tests/test_d_*.py`. NO toques: `tools/paper/{community,essays,essay_doc}.py`, `tools/paper/templates/essay.py`,
`site-src/assets/css/essay.css`, `site-src/assets/css/d/d-letters.css` (carril nl-d-cartas). layout.py debe enlazar
d-base/d-front/d-story/d-letters/d-pages (d-pages también es tuyo si lo usas).

## Cómo
1. Componentes compartidos del contrato (`.d-grade`, `.d-claim--*`, `.d-stat`, `.d-evidence-map` SVG desde datos,
   `.d-ledger`, `.d-claims-sources`, `.d-timeline`, `.d-legend`, `.d-rank`, `.d-kicker`, `.d-section`, `.d-nav`, `.d-footer`)
   en `templates/d_components.py` + d-base.css, con pruebas unitarias de variantes (0/1/n fuentes, afirmaciones y huecos;
   sin imagen; titular largo; 中文).
2. Portada, historia, archivo, método/institucionales, búsqueda y temas con esos componentes.
3. Construye el sitio con fixtures del repo (`_fixtures/`, mira cómo lo hacen los tests y `contracts/`) y toma capturas
   1440/390/320 de cada tipo de página; compáralas con la referencia y corrige hasta que coincidan en retícula, jerarquía y
   proporciones. Guarda las capturas en `design/d-libro/capturas/core/` (PNG ≤ 400 KB c/u, recorta si hace falta).
   Si el sandbox no permite navegador, deja el comando exacto en NEEDS.md y sigue con lo demás.

## Aceptación
- `python3 -m unittest discover -s tests` sin fallos nuevos frente a origin/main (guarda conteos antes/después);
  `python3 design/check_contrast.py` OK; tests `tests/test_d_*.py` verdes.
- Ningún texto inventado (cargos, nombres, fechas, conteos): todo trazable a datos. Mêtis sólo en los usos del contrato.
- `git diff --stat` dentro de tu lista de dueño.

## Prohibido
Secretos, deploy, push, tocar archivos del otro carril, debilitar gates de privacidad/legal/i18n/publicación (AGENTS.md).
Reporte final ≤10 líneas: COMMITS, FINDINGS, ACCEPTANCE (con conteos), UNVERIFIED, CANON (sólo lo que leíste).

Nota (relanzamiento 10-26): un intento anterior se cortó y pudo dejar trabajo parcial sin commit (mira `git status`); revísalo y continúa, no lo descartes sin razón. La carpeta del brief ahora es escribible.
