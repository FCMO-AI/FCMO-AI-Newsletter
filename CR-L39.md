# CR-L39 — recibo actualizado antes de publicar

La reparación local está implementada en `c5/l39-receipt`. La edición 2026-10-07
permanece en los datos fuente; su publicación todavía requiere PR, CI, merge,
Deploy y verificación del origen público. Esta caja no tiene sesión de GitHub:
`gh auth status` devuelve código 1 y «You are not logged into any GitHub hosts».
Se aplica la salida local expresamente prevista en L39; no se ha hecho push,
creado PR, fusionado ni despachado workflows.

## Causa comprobada

`tools/build_ready_receipt.py` escribe `READY_TO_PUBLISH.md`. Construye un árbol
temporal con `tools/paper/build.py`, sin contenido editorial humano, y mide las
rutas finales, las copias exactas de Story/estado y todos los bytes del árbol.
Su opción `--check` reconstruye y compara; nunca reescribe.

Antes del cambio, `daily-refresh.yml` sólo actualizaba Story/estado y conservaba
`READY_TO_PUBLISH.md` en su lista de staging. Ninguno de sus caminos, `rebuild`
o `status`, ejecutaba el generador. Pages y `ops/publish.py` ejecutaban
`tools/verify_release.py`, que exige ese recibo mediante `--check`, sin prepararlo.
El oráculo de refresco sí lo generaba en su copia de pruebas: ese camino verde
no demostraba la misma operación en producción.

Una modificación del renderizador cambia los bytes registrados; un merge no
regenera archivos derivados; una actualización de `newsroom-status.json`
cambia el hash de estado y los `lastmod` de rutas. El commit base `9468c9e`
actualizó únicamente `site/data/newsroom-status.json`. Un Refresh exitoso no
podía reparar el recibo porque carecía del paso de generación.

## Antes y después

En el árbol original, `python3 tools/build_ready_receipt.py --check` salió 1:

| Entrada | Recibo obsoleto | Árbol local medido |
| --- | --- | --- |
| Rutas | `3960d477…` | `05ecdbe2…` |
| Estado | `a008f936…` | `34949fd9…` |
| Candidato | `91846c44…` | `09ba0b09…` |

Rutas y estado reproducen los hashes del brief. El hash total local difiere del
`3e25df05…` observado en Actions; no se afirma identidad entre aquellos árboles.
Dos reconstrucciones locales independientes produjeron `09ba0b09…`.

El commit rojo `d94a556` incorpora cuatro regresiones: tres fallos y un error
antes de la corrección. Cubren orden en Deploy, los dos caminos de Refresh,
`ops/publish.py --check` y la validación de snapshots congelados.

La corrección añade generación antes de `verify_release.py` en Pages y ambos
caminos locales de publicación. Refresh genera y comprueba después de escribir
el estado, antes de su commit. También se actualiza el recibo fuente. No se ha
cambiado `tools/verify_release.py`, el generador del recibo ni su comprobación.
Está en el commit `c1a2789`, con autor `Codex <noreply@openai.com>`.

La regresión comprueba que una modificación posterior del HTML sigue fallando
por `candidate_sha256` y que `--check` deja intacto el recibo. La generación
repetida conserva exactamente sus bytes. Las 46 pruebas focalizadas pasan.

## Verificación de aceptación

- `python3 -m unittest discover -s tests`: **PASS**, 830 pruebas en 442.643 s,
  cuatro omisiones automáticas del entorno.
- Repetición con Chromium disponible: **PASS**, 830 pruebas en 336.725 s,
  dos omisiones automáticas.
- `tools/verify_release.py` dentro de `ops/publish.py --check`: **7/7**,
  incluido `recibo contra el arbol`.
- Candidato `/tmp/l39`: **14/14** gates deterministas; 618 rutas,
  `edition_date=2026-10-07`, `edition_state=FRESH`.
- Matriz final de navegador: **PASS**, tres idiomas × dos viewports; presupuestos
  de layout sobre 150 rutas Story, tres portadas y 206 páginas ZH.
- `ops/publish.py --check --out /tmp/l39`: **salida 0**, suite, integridad y
  navegador completos.

Comando reproducible utilizado en esta caja, con la caché de Chromium local:

```sh
C=/srv/fcmo/agents/work/newsletter/c5
PLAYWRIGHT_BROWSERS_PATH="$PWD/__pycache__/l39-browser" \
PLAYWRIGHT_MODULE="$C/node-pw/node_modules/playwright" \
PATH="$C/venv-pw/bin:$PATH" \
python3 ops/publish.py --check --out /tmp/l39
```

La caché es un artefacto ignorado del worktree. Fuera de esta caja se puede
usar la instalación de Chromium del verificador. Los logs locales están en
`/tmp/l39-unittest.log` y `/tmp/l39-publish-browser.log`; no se incluyen en Git.

El primer intento con Playwright encontró el paquete instalado pero sin
Chromium: 830 pruebas, dos fallos por `BROWSER_UNAVAILABLE`, dos omisiones.
Se descargó el navegador dentro del worktree, sin cambiar las dependencias
compartidas ni las de CI. La prueba negativa de overflow y la prueba de primer
viewport real ya pasan con ese ejecutable. No se omitió ni relajó el oráculo.

## Continuación autorizada fuera de esta caja

Tras repetir las comprobaciones sobre esta rama con autenticación disponible:

1. `git push -u origin c5/l39-receipt`.
2. Crear PR hacia `main`; esperar todos los checks requeridos y revisiones que
   exija la protección vigente.
3. Con CI verde, `gh pr merge NUMERO --merge --repo FCMO-AI/FCMO-AI-Newsletter`.
4. Despachar Refresh en `main` si se necesita actualizar Story/estado; su éxito
   encadena Pages. También se puede despachar Deploy explícitamente con
   `gh workflow run pages.yml --repo FCMO-AI/FCMO-AI-Newsletter --ref main -f operation=deploy`.
5. Esperar build, deploy, verificación pública y promoción LKG. Confirmar que
   `https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/newsroom-status.json`
   contiene `edition_date >= 2026-10-07` y que la identidad pública corresponde
   al candidato aprobado. Inspeccionar la edición renderizada EN/ES/ZH.

Los archivos externos `STATE-AND-PLAN.md`, `PLAN.md` y `OPERADOR.md` indicados en
las reglas comunes no están disponibles en sus rutas en esta caja. Se leyó el
contrato L39, la doctrina local y del Hub y las notas de Newsletter disponibles.

**Resumen:** corrección local verificada: suite, integridad 7/7, gates 14/14
y navegador pasan. Publicación real pendiente de autenticación y prueba pública.
