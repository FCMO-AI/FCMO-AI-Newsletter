# Suscripciones de FCMO

## Qué está preparado

Ghost administra **una membresía** y dos newsletters independientes. `community/config/subscriptions.json` es la fuente de nombres, slugs, autores e idiomas pendientes de O-11. La carta pertenece a fCMO y Javier; el resumen técnico pertenece a FCMO AI y Matías. El lector debe poder elegir una o ambas y cambiar la selección desde `/#/portal/account` en Ghost. El papel estático no recibe ni guarda correos.

`tools/paper/templates/subscribe.py` ofrece `subscribe_block(zone, locale)` para `letter`, `paper` o `all`. La portada y `/suscribete/` lo reciben hoy por `tools/paper/community.py`. Sin `GHOST_URL`, la página avisa que el alta abrirá en el lanzamiento y enlaza RSS, Atom y JSON Feed. Con una URL HTTPS válida (o loopback de staging), solo `es-419` muestra el enlace de alta. `en` y `zh-Hans` conservan los feeds hasta la decisión O-11. El enlace directo a Ghost Portal funciona sin JavaScript. La selección de newsletters y el enlace mágico son responsabilidad de Ghost Portal; la prueba local debe demostrar que ofrece controles separados antes de hacer público `GHOST_URL`.

Los textos españoles para confirmación y bienvenida, separados por marca, están en `community/config/member_messages.es.json`. Son copy listo para configurar en Ghost, **no prueba de que Ghost 5 permita dos plantillas de confirmación o bienvenida distintas por newsletter**. Ghost envía el correo transaccional y el opt-in; no simular doble opt-in con una lista local. Si Ghost solo admite un mensaje de confirmación global, usar uno neutral que nombre las dos publicaciones y conservar el copy por marca para las páginas de bienvenida. No activar una promesa de secuencia automatizada sin verificar el soporte de Ghost.

El resumen técnico usa `tools/email_render.py`, con colores del sistema v2 y el nombre de `community/config/subscriptions.json`. `tools/email_dispatch.py` apunta preferencia y baja a `GHOST_URL/#/portal/account`; Ghost añade sus propias cabeceras de baja al envío. La carta se redacta y envía desde Ghost con la plantilla editorial del tema. El envío del resumen técnico sigue condicionado por edición fresca, español completo, live verify y horario.

## Prueba local antes del corte

1. Ejecutar `ops/staging/ghost-staging.sh up` fuera del sandbox. Ghost 5 queda solo en `127.0.0.1:2368`; Mailpit UI y SMTP solo en `127.0.0.1:8025` y `127.0.0.1:1025`. El SMTP entre contenedores usa la red privada de Podman.
2. Completar el asistente local en `/ghost/`; habilitar membresías, Portal y newsletters, y exigir confirmación del correo. Crear una integración personalizada con alcance Admin API. Guardar **solo** su key en `ops/staging/.state/admin-api-key` con modo 600. `.state/` está ignorado por Git.
3. Disponer de Node, `playwright-core` y Chromium locales. Definir `PLAYWRIGHT_CORE` como ruta al paquete si no está en el path de Node, y `CHROMIUM_PATH` si hace falta. Ejecutar `python3 ops/staging/e2e_subscribe.py`. Este programa crea las dos newsletters por Admin API, desactiva extras, construye el sitio con `GHOST_URL`, prueba las combinaciones carta, resumen y ambas, sigue el enlace de Mailpit, compara las newsletters del miembro en Admin API, y comprueba la baja. Cualquier selector o endpoint que cambie hace fallar la prueba; no equivale a PASS hasta que corra con Ghost real.
4. Revisar el correo recibido y el Portal en navegador a 390 y 1440 px. Ejecutar `ops/staging/ghost-staging.sh down`; `down --purge` destruye además el volumen y las claves locales.

## Corte de producción, cuando se decidan O-6, O-7 y O-9

1. **O-6**: contratar Ghost(Pro) con Admin API, una sola instancia y las dos newsletters. Crear las cuentas de staff de Javier y Matías por la interfaz de Ghost; configurar entrega, Portal, confirmación, remitentes y membresía gratuita. Ejecutar en staging real la misma matriz de alta/preferencias/baja. Guardar `GHOST_ADMIN_API_KEY` solo como secret del environment `email` de GitHub Actions; `GHOST_URL` como secret de `email` para el dispatch y como variable de build para el CTA. `GHOST_CONTENT_API_KEY` es variable de build del rail de cartas. No poner claves en HTML ni en el repositorio.
2. **O-7**: conectar dominio HTTPS de Ghost y del periódico; verificar la propiedad DNS y el envío SPF, DKIM y DMARC. Cambiar solo los valores de URL (`GHOST_URL`, `GHOST_CONTENT_URL`, `FCMO_SITE_URL`) y probar el sitio en el origen público. No activar el CTA en un build que apunta a staging.
3. **O-9**: completar responsable de datos, domicilio, buzón de privacidad y dirección postal de email. Poner `FCMO_EMAIL_POSTAL_ADDRESS` como secret del environment `email`. Publicar el aviso de privacidad revisado antes del primer miembro real. O-15 recomienda revisión legal. La decisión O-11 sobre idiomas se refleja en `languages.signup_locales` y `languages.email`; el email sigue en español hasta decisión explícita.
4. Activar el build con `GHOST_URL` después de observar alta doble, bienvenida, preferencias y baja en Ghost real. Verificar desde el sitio público y un buzón de prueba de O-10; revisar que los headers de unsubscribe y autenticación de correo son reales. Mantener el CTA cerrado si falla cualquiera de estas comprobaciones.

## Fallos y recuperación

- Ghost ausente, URL inválida u otro idioma sin aprobación: página honesta de lanzamiento y feeds, sin formulario muerto.
- Ghost caído después del build: el enlace directo falla fuera del control del sitio estático. Monitorear Ghost y volver a publicar sin `GHOST_URL` si el fallo persiste; el rail de cartas ya se omite cuando falla Content API.
- Mailpit sin enlace mágico o Admin API con newsletters equivocadas: no activar el CTA. El script de staging falla de forma explícita.
- La cuenta de Ghost incluye opciones de newsletter diferentes a las del sitio: corregir la configuración de Ghost antes de promover el build.
- Domicilio o aviso incompleto: no iniciar envíos reales. El dispatch rechaza domicilio vacío.
- Edición técnica retrasada: el dispatch no envía. Una carta humana de Javier sigue su propio flujo editorial en Ghost.
