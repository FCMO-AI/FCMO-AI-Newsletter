# CR-L40 — Studio funciona en loopback; activación tailnet pendiente

Studio respondió en **127.0.0.1:8490** mediante el launcher real y pasó tareas de
escritura, guardado/recarga, vista previa con el renderer de producción, revisión
con otra sesión y manejo de desconexión. Se preparó el único URL
**https://fcmo-hub.tail8cbe0b.ts.net:8447/**. No se instaló systemd ni se añadió
el mapping desde esta lane; la línea ejecutable está en [OPERATOR-LINE.md](OPERATOR-LINE.md).

## COMMITS

Se continuó el trabajo previo y se integró `origin/main` mediante fast-forward a
`9468c9e` antes de modificar archivos. Commits de implementación:

- `75027f8` — Fix quoted Studio credential paths during user installation.
- `ead71d8` — Prepare guarded single URL Studio host activation.
- `f63ef5a` — Clarify private Studio review and refuse unread publication mode.

El intento autorizado de `git push -u origin c5/studio-live` fue rechazado por
falta de autenticación: Git no pudo obtener el usuario de HTTPS. La entrega queda
en commits locales, sin push confirmado ni PR. No se extrajeron credenciales ni
se intentó otra identidad.

## FINDINGS CLOSED

Identificadores locales de este informe; el brief no cita findings de un audit.

- **L40-INSTALL:** el instalador interpreta las asignaciones literales generadas
  por `prepare_host.py`, incluidas rutas entre comillas. La prueba
  `QuotedEnvironment.test_install_accepts_shell_quoted_personal_directories`
  falló primero con el rechazo de una ruta válida y pasó después. No se ejecuta
  contenido del entorno para analizarlo.
- **L40-HOST:** unidad canónica bajo `ops/studio/`, referencia compatible desde
  `studio/host-ops/`, preflight de origen/puerto, bundle actual, datos fuera del
  checkout, permisos privados y ambas cuentas locales. `SingleURLHost` falló
  primero porque faltaba esta preparación; ahora prueba los rechazos y consulta
  health, HTML, JS/CSS y API protegida por HTTP real. El instalador conserva su
  recibo y rollback anteriores. El comando de Tailscale sólo se ejecuta después
  de comprobar el servicio durante hasta 45 segundos.
- **L40-MODE:** el modo privado deja de prometer publicación pública. La hoja
  y la confirmación distinguen la aprobación privada; el estado no leído
  deshabilita la aprobación, explica el límite y permite volver a comprobar.
  `studio_host_task.mjs` falló primero al faltar el aviso de modo privado y luego
  al permitir aprobar sin poder leer el modo. El recorrido final pasó ambos
  casos, incluida la recuperación y la aprobación por la otra sesión.

## FINDINGS NOT CLOSED

- **L40-TAILNET:** systemd de usuario devuelve `offline`; no existe el socket
  local del daemon de Tailscale en esta sesión. El brief pide entregar la unidad
  sin instalarla y reserva el mapping al operador. No se afirma que el URL esté
  sirviendo ni que Javier haya entrado. Debe ejecutarse la línea y probar HTTPS,
  TLS/ACL, ambas cuentas y el teléfono desde el host.
- **L40-PUBLICATION:** no se probaron cuentas reales de GitHub, protecciones
  remotas, backup de producción ni un PR editorial/Pages/origen público real.
  Conservar dry-run hasta completar la activación existente. Esta lane no cambia
  los gates ni añade excepciones de publicación.

## ACCEPTANCE

Los módulos de Playwright, Chromium y axe utilizados ya estaban instalados; no
se añadieron dependencias. Evidencia externa en `../../reports/studio-frames/`.

| Comando | Resultado observado |
| --- | --- |
| `git fetch origin main` y `git merge --no-edit origin/main` | Fast-forward a `9468c9e` |
| `python3 -m unittest discover -s tests -p 'test_studio*.py'` antes de cambios | 85 tests, OK; un skip condicional |
| `python3 -m unittest discover -s tests` | 830 tests, OK; dos skips, 403.065 s |
| `python3 -m unittest tests.test_studio_host tests.test_studio_activation` final | 12 tests, OK |
| `node --test studio/web/test/*.test.mjs` | 9/9, sin skips |
| `python3 -m tests.harness.studio_host_journey --out ../../reports/studio-frames` con el Playwright existente | Completado: loopback, 51 comprobaciones, 46 capturas |
| Regresiones browser del recorrido | Editor 12/12, comentarios móviles 4/4, idiomas 7/7, hoja de publicación 7/7, credenciales 6/6; drag 3/3 y recuperación de buffer 3/3 incluidos en editor |
| `PYTHONPATH=tests python3 -m unittest harness.test_harness_tools.BrowserRunTests` con NODE_PATH y AXE_CORE_PATH existentes | 3/3, sin skips; completa la clase omitida por configuración en la suite amplia |
| `systemd-analyze --user verify ops/studio/fcmo-studio.service` con runtime temporal | Exit 0; no instala ni inicia un gestor |
| `git diff --check`, integridad del bundle y `NO_MACHINE_PATHS` | PASS |
| `git push -u origin c5/studio-live` | Exit 128: autenticación HTTPS no disponible; no se creó PR |

`journey.json` registra `completed: true`, las cinco regresiones y el SHA-256
del manifest del bundle servido:
`0c2bb3f931b214cfee202e9f949f0ea9a27dd8d43fbf9abb961aaf0916d2651e`.
`acceptance.json` enumera las 46 capturas y las 51 comprobaciones. Se inspeccionaron
escritorio, editor, idiomas ES/ZH, vista previa, revisión, progreso y el rechazo
de modo no leído. Los flujos principales se capturaron a 1440 y 390 px, claro y
oscuro; sus 40 comprobaciones de overflow y cuatro de errores de navegador pasan.

La prueba usa almacenamiento y cuentas temporales, git local y una inyección
explícita del límite del remoto para el launcher. El editor, HTTP, autenticación,
persistencia y renderer son reales. No hay dev API, respuestas de modelos,
transporte GitHub real, secretos del host ni escrituras a borradores de producción.
Los servidores temporales se cerraron al terminar.

La primera suite amplia detectó un path de host en la línea operativa y una
lectura concurrente durante el rebuild del bundle. Se retiró el path del documento
y se repitió la suite con los artefactos presentes, sin modificar los gates ni
las aserciones. El oracle móvil pasó también por separado en `origin/main` y
en este checkout. No queda un fallo del periódico móvil demostrado por esta lane.

## UNVERIFIED

Instalación permanente, reinicio/persistencia de systemd, mapping Tailscale,
DNS/TLS/ACL y uso por Javier desde su dispositivo. Publicación real y sus
prerrequisitos de credenciales/protecciones/backup. El único caso condicional
que sigue sin ejecutarse es el negativo del renderer ausente: el renderer está
presente y su identidad se prueba en el caso positivo. No se afirma un nuevo
ciclo autónomo ni nueva frescura del periódico público.

## NEEDS.md

Se añadió únicamente la entrada **L40 — activación de Studio en el host**. El
contenido previo queda conservado. Contiene la ubicación de la unidad, el límite
de systemd/Tailscale, la preparación privada, la línea exacta, las pruebas de
HTTPS/dispositivo pendientes y la obligación de conservar dry-run hasta probar
la publicación protegida. Ver [NEEDS.md](NEEDS.md).

## KNOWN GAPS

El resultado entregado es un Studio privado comprobado en loopback y una
activación de host preparada. El URL tailnet todavía requiere efecto y prueba
del operador. Las capturas son del camino local con cuentas temporales; no son
aceptación de Javier o Matías ni prueba de publicación remota.
