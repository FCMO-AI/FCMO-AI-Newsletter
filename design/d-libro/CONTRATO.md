# D «Libro de evidencias» — contrato de construcción (Claude, 2026-10-26)

Matías aprobó D y pidió (2026-10-26, textual): «Queremos que Newsletter sea un verdadero 1:1 de esas imágenes, y que lleve
esos diseños en todo su esplendor a producción, todo bajo un sistema automatizado, diseños flexibles y variables».

## Referencias (la verdad visual)
`/var/tmp/kyrion-test/c7/r4/` (montado sólo lectura): R4-portada, R4-historia, R4-cartas, R4-carta, R4-archivo, R4-metodo
(escritorio ~1440) y R4-movil-portada, R4-movil-carta (390). Ábrelas y míralas antes de escribir CSS. 1:1 = misma retícula,
jerarquía, proporciones, pesos, reglas, espacios y componentes. El texto de las imágenes es de ejemplo: el contenido sale de los datos.

## Ley visual (Hub `identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt` manda)
- Superficies: Ink #0A0A0A (≥60 %, fondo principal) y Bone #F2EFE8 (bandas claras: leyenda, correcciones, cartas). Máx. 2.
  Texto secundario Stone #8A857C, Fog #D9D5CC, reglas Rule DK #2A2A28 sobre Ink y Fog sobre Bone; cuerpo sobre Bone Body #3A3A38.
- Tipografía SÓLO Inter Tight (900/700/400) y JetBrains Mono (metadatos, etiquetas, fechas, grados). Fuera Source Serif.
- Sin gradientes, sin sombras, esquinas rectas, reglas de 1px. Imágenes: plates mate cinematográficos existentes (plates.py).
- Mêtis #F05A28 = chispa de inteligencia/ejecución, nunca relleno, fondo, titular ni categoría. Usos permitidos (los de la
  referencia): subrayado del nav activo, marcador del #1, cuadrito del kicker de la nota principal, el paso «ahora» de una
  línea de tiempo, la arista izquierda del ítem activo de un ledger, el circunflejo de marca. Pocos por pantalla.
- True colors SÓLO como cuadritos de señal de tema/diagrama: Intelligence #5B7C93, Foundry #BB5E4A, Living #73875A
  (mapa tema→color en datos; tema sin mapa = Stone). Nunca texto largo ni superficies.

## Vocabulario de evidencia (componentes compartidos; nombres de clase fijos)
- `.d-grade` cuadro con letra de grado de fuente (A, B…) + etiqueta mono; `.d-claim--shown` (cuadro sólido),
  `.d-claim--claimed` (cuadro rayado diagonal), `.d-claim--not-established` (cuadro punteado). Mismo dibujo en todo el sitio.
- `.d-stat` número grande + etiqueta mono («1 primary source», «2 open gaps»).
- `.d-evidence-map` diagrama SVG generado desde datos: fuente(s) primaria(s) → afirmación → huecos abiertos (punteados).
- `.d-ledger` lista numerada 01/02/03 de afirmaciones con su estado; `.d-claims-sources` diagrama afirmaciones↔fuentes;
  `.d-timeline` puntos con fecha; `.d-legend` banda Bone «Shown. Claimed. Not established.»; `.d-rank` tabla «in order of importance».
- `.d-kicker` línea mono en mayúsculas; `.d-section` encabezado de sección (Inter Tight 700 mayúsculas + regla).
- Nav `.d-nav` (marca cuadro+FCMO AI, Today/Letters/Topics/Archive/Method/Search, EN/ES/中文, Subscribe) y pie `.d-footer`.

## Sistema automatizado, flexible y variable (no plantillas fijas)
- Todo sale de los datos ya existentes (stories, evidencia, fuentes, huecos, correcciones, ediciones, cartas/pieces, i18n).
  El mapa de evidencia, el ledger, el diagrama y la línea de tiempo se dibujan con el número real de fuentes/afirmaciones/huecos
  (1..n), sin desbordarse; si no hay datos, el bloque desaparece o muestra su estado vacío honesto.
- Variantes por contenido: titular largo/corto (escala tipográfica fluida), nota sin imagen → héroe tipográfico, 1..N notas
  en la tabla, 0..N cartas, ediciones vacías. Tres idiomas (EN/ES/中文) sin cortes.
- Prohibido inventar: cargos, nombres, fechas, conteos o textos que no estén en los datos (en R4 había «Research editor»,
  «M. Ortega» y fechas 2024: son defectos de la imagen, no se copian). Sin carta real → no hay tarjeta.
- Accesible: contraste AA (design/check_contrast.py), foco visible, objetivos ≥44 px en móvil, sin scroll horizontal a 320.

## CSS (dueños disjuntos)
`site-src/assets/css/d/`: d-base (tokens, nav, pie, componentes de evidencia) · d-front · d-story → carril nl-d-core;
d-letters → nl-d-cartas; d-pages → nl-d-paginas. Nadie edita el archivo de otro; si falta algo compartido, se pide en
NEEDS.md con el nombre de clase. paper.css viejo se retira al integrar (lo decide el integrador).

## Verdad de «listo»
Capturas reales 1440/390/320 de cada tipo de página junto a su referencia (tools/paper/playwright_module.py o Chromium
headless del host), suite `python3 -m unittest discover -s tests` sin fallos nuevos, y juicio visual de Claude.
