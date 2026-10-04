# L16-mobile — primera pantalla y desbordamiento zh-Hans

## Cambio

- La navegación móvil conserva una sola fila en 390 px: ajusté el tamaño y el espacio de los enlaces y oculté solo las rutas duplicadas que ya ofrece el logotipo o el selector de secciones. Los destinos siguen alcanzables desde el encabezado.
- `.brand-sub` vuelve a mostrarse en escritorio; permanece oculto en móvil para conservar el cromo compacto.
- El contenido de `.story-body` ahora permite partir cadenas largas en cualquier punto. Los bloques `pre`, tablas y `.math-display` tienen desplazamiento horizontal local, para que contenido técnico ancho no ensanche la página.
- No edité la historia de Navier–Stokes ni cambié los límites del oráculo.

## Causa y medidas

El registro de campaña en `MISSION.md` da estos valores previos observados en el host: titular móvil alrededor de **296 px** desde arriba, navegación en **2 filas**, y `.brand-sub` oculto en escritorio. El barrido L10 registró **419 px de scrollWidth frente a 390 px de viewport** en la historia Navier–Stokes de zh-Hans.

En el HTML generado encontré el identificador de commit `8bf45ed70d48b2b2a501de9c00b26bfa38c573ee` (40 caracteres) repetido como texto continuo en párrafos técnicos. La regla de ajuste de línea aplica a todo el cuerpo de una historia, no a ese texto ni a esa ruta en particular.

En el CSS candidato, la navegación móvil tiene `font-size: 0.65rem` (**10.4 px**) y `min-height: 2.35rem` (**37.6 px**), menor que el límite de alto del nav del oráculo (**48 px**). Son valores de estilo, no una medición del navegador. No pude obtener una posición posterior del h1 ni un `scrollWidth` posterior: no hay módulo Playwright resoluble ni Chromium en esta caja. Por tanto, la mejora visual y el cero desbordamiento siguen pendientes de prueba en el host.

## Verificación

- Rojo primero: las dos nuevas pruebas CSS fallaron antes del cambio porque no existían el override de navegación/subtítulo ni el ajuste de cadenas largas.
- `python3 -m unittest discover -s tests -p 'test_v4_mobile_first_viewport.py'` — **16 OK, 1 omitida**.
- `python3 -m unittest discover -s tests -p 'test_v3_integration.py'` — **4 OK**.
- `python3 -m unittest discover -s tests` — **583 OK, 3 omitidas**.
- Build a `/tmp/newsletter-mobile-after` — **468 rutas, 57 feeds, 354 redirecciones**; confirmé que el CSS construido contiene el ajuste genérico y los overrides finales.
- `git diff --check` — OK.
- `python3 tests/oraculos/verificar_mobile_first_viewport.py` — **no verificable aquí**: `BROWSER_UNAVAILABLE`, módulo Playwright sin resolver. No se afirma que el oráculo haya pasado.

## Continuación del arquitecto en host

Con un módulo Playwright y Chromium ya instalados, ejecutar el oráculo completo para las tres locales y revisar sus medidas:

```sh
python3 tests/oraculos/verificar_mobile_first_viewport.py \
  --playwright-module /ruta/al/node_modules/playwright \
  --print-measurements
```

Para la ruta específica del desbordamiento, construir el candidato bajo el prefijo de Pages, servir el directorio padre y correr el harness existente:

```sh
mkdir -p /tmp/newsletter-mobile/FCMO-AI-Newsletter
python3 tools/paper/build.py \
  --stories site/data/stories.v2.json \
  --status site/data/newsroom-status.json \
  --out /tmp/newsletter-mobile/FCMO-AI-Newsletter \
  --base /FCMO-AI-Newsletter/
python3 -m http.server 8765 --directory /tmp/newsletter-mobile
```

En otra terminal, sustituir `/ruta/al/node_modules/playwright` por el módulo del host:

```sh
PLAYWRIGHT_MODULE=/ruta/al/node_modules/playwright \
node tests/harness/browser/overflow.mjs \
  http://127.0.0.1:8765/FCMO-AI-Newsletter/zh/2026/09/13/openai-publishes-an-ai-generated-proposed-navier-stokes-millennium/ \
  --viewport 390x844 --tolerance 1
```

El arquitecto debe confirmar `scrollWidth == clientWidth`, nav en una fila, h1 dentro del límite, `.brand-sub` visible a 1440 px, cero errores de consola y gates del oráculo antes de considerar la afirmación visual cerrada.

Resumen: la corrección está implementada y la suite completa pasa; falta la prueba visual real en Chromium del host.
