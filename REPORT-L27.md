# L27 — Diario automático por correo, Kit primero

**Implementación local lista para revisión; Kit, la entrega real y la publicación siguen sin activar. No se hizo push ni se contactó ningún proveedor.** Los adaptadores `kit`, `listmonk` y `fake` comparten formulario, envío por edición/idioma, exportación y health. Se conserva L26: no se borran su gateway, consentimiento, journal, instalación, backup ni SES.

La decisión de usar el plan gratuito de Kit (hasta 10.000 lectores y envíos ilimitados) viene del operador. **No pude comprobar que ese plan permita programar broadcasts con API v4.** Esa capacidad es imprescindible para enviar sin pulsar Send. Claude debe confirmarla con la cuenta/key real antes de activar: que la interfaz ofrezca envíos ilimitados no prueba que el endpoint esté habilitado. Si devuelve una restricción de plan, no hay automatización real con esta ruta hasta resolverla; Listmonk de L26 permanece como alternativa configurable. No se contrató ni se autorizó un plan de pago.

## Resultado y decisiones

- `FCMO_EMAIL_PROVIDER` selecciona el módulo por nombre. La interfaz y los workflows no necesitan modificarse para agregar otro adaptador bajo el mismo contrato; la configuración adicional puede viajar en `FCMO_EMAIL_PUBLIC_CONFIG` (pública) y `FCMO_EMAIL_PROVIDER_CONFIG` (secret). El adaptador aporta su aviso de privacidad curado. [Contrato y migración](docs/EMAIL-PROVIDERS.md).
- Kit usa **tres formularios y tres etiquetas**, uno por idioma. Así el HTML puede hacer POST directo sin servidor propio, scripts externos ni una selección que termine enviando al formulario equivocado. La página muestra el idioma de su edición; el selector del periódico permite cambiarlo. Las etiquetas se asignan desde Kit y filtran el broadcast. Cada formulario debe asignar su etiqueta tras la confirmación. Si la cuenta gratuita no permite esta configuración, confirmar una alternativa de filtrado por formulario en el adaptador; no simular una etiqueta que nunca se asigna.
- Se mantiene el checkbox obligatorio y desmarcado y ambos enlaces de privacidad. Kit controla la confirmación y las bajas. **El checkbox es una restricción del navegador, no una prueba de enforcement del servidor de Kit.** No se promete el registro de consentimiento propio del gateway de L26. El operador debe comprobar los registros de formulario/confirmación disponibles y la suficiencia del consentimiento antes de recoger lectores reales.
- Actions conserva el gate de L26: LKG promovido, identidad live, hashes de todas las rutas críticas, entradas obtenidas de esa misma publicación, fecha del día en Ciudad de México, después de las 07:30, noticias nuevas y contenido nativo completo en los tres idiomas. Primero valida la edición y health/configuración; después persiste un intent; después invoca el adaptador por locale. No hay traducción durante el envío.
- Un broadcast lleva `description=fcmo-diario:<fecha>:<locale>`, `public=false`, HTML de L26, filtro de una etiqueta y `send_at` UTC. Se relee el estado del proveedor. `QUEUED` significa campaña observada/programada, no entrega ni inbox placement.
- **Mejora sobre la búsqueda simple propuesta:** Actions sube un intent antes de cualquier POST y restaura los del mismo día en ejecuciones/reintentos posteriores. Un POST con 429/5xx/timeout se intenta una sola vez y se reconcilia mediante GET; no se repite a ciegas. Los GET tienen tres intentos como máximo, timeout de 25 s y pausas de 1/2 s. Si existe intent pero no aparece el broadcast, se bloquea su recreación. Se intenta cada locale para que un error de EN no impida comprobar ES/ZH en la misma ejecución. Un snapshot anterior reserva las tres claves: un runner perdido antes de enviar puede exigir reconciliación aunque no se haya creado nada. Esta conservación es deliberada ante la falta de idempotencia transaccional confirmada en Kit.
- El backup diario usa el mismo adaptador. Consulta estados de suscripción y membresías, pasa JSON por memoria/pipe a age y escribe/sube exclusivamente `.age`. Retención: 30 días. No hay listas claras en repo, ramas, disco del runner, artefactos ni logs. La identidad de descifrado queda fuera de GitHub. El backup del host de L26 sigue vigente.

## Configuración de Kit: recorrido para el operador

Los siguientes son los clics esperados de Kit; **la interfaz no se abrió en esta sesión**. Claude debe confirmar los nombres vigentes y dejar evidencia privada de la configuración, sin publicar key, correo personal ni lista.

1. Entrar en **kit.com → Get started / Sign up**. Crear la cuenta con el correo del operador, confirmar ese correo y elegir **Newsletter / Free**, evitando contratar automáticamente una prueba/plan de pago. Confirmar en **Settings → Billing** los límites efectivos y el acceso de API necesario.
2. Abrir el menú de cuenta/avatar → **Settings → Developer → API keys → Create API key**. Crear una key **v4**, copiarla una vez a `KIT_API_KEY` del environment `email` de GitHub. No usar la API secret/key v3, OAuth ni Authorization Bearer: el adaptador usa `X-Kit-Api-Key`.
3. **Grow → Subscribers → Tags → Create tag**: crear `diario-en`, `diario-es-419`, `diario-zh-Hans`. Anotar los IDs numéricos, confirmándolos por API `GET /v4/tags` si la UI no los muestra. No confundir ID con nombre.
4. **Grow → Landing Pages & Forms → Create new → Form → Inline**: crear tres formularios con nombres `Diario EN`, `Diario ES`, `Diario ZH`. Dentro de cada uno, abrir **Settings → Incentive**: activar **Send incentive email** y dejar **Auto-confirm new subscribers** desmarcado. Curar asunto, instrucciones y botón de confirmación en el idioma correspondiente. Usar confirmación sin descarga ficticia. En **Settings → General**, elegir una página de confirmación/éxito adecuada.
5. En el editor **Publish / Embed → HTML**, comprobar la acción pública exacta y el campo de email. Esta implementación espera `https://app.kit.com/forms/<ID>/subscriptions` y `email_address`. Guardar los tres IDs como `KIT_FORM_EN/ES/ZH`. Si el HTML vigente usa otro host, campo o endpoint, corregir exclusivamente el adaptador y volver a probar; no activar un formulario basándose solo en su ID.
6. **Automate → Rules → New rule** (o el editor de automatización equivalente): trigger **Subscribes to a form**, seleccionar el formulario de ese idioma; action **Add tag**, seleccionar su etiqueta. Repetir para los tres. Probar que un pendiente no reciba broadcasts y que un confirmado entre en la etiqueta correcta. Confirmar que el plan permite las tres asignaciones. Si se desea una sola lengua por lector, añadir la retirada de las otras dos etiquetas al elegir idioma y comprobar que no se conserva una membresía accidental. Un lector con varias etiquetas recibirá varias versiones.
7. **Settings → Email → Sending email address / Add email address**: introducir el remitente editorial, pulsar **Verify / Send verification**, abrir su correo y confirmar. Poner esa dirección confirmada, sin display name, en `FCMO_EMAIL_FROM`. Configurar nombre visible, dirección postal real y contacto de privacidad en la cuenta. Desactivar seguimiento de aperturas/clics en los ajustes de envío y confirmar que los broadcasts de API heredan ese comportamiento. Confirmar footer, baja visible, baja de un clic y supresión de rebotes/quejas en la cuenta real.
8. Opcional para el primer seed y recomendable para producción: **Settings → Email → Verified sending domains → Add domain / Set up**. Copiar en el DNS **exactamente** los registros SPF/DKIM que genere esa cuenta y confirmar **Verify**. Configurar DMARC según el dominio y sus otros remitentes, sin duplicar SPF. No se inventan selectores DNS: dependen de la cuenta/dominio real. Inspeccionar autenticación y alineación en el mensaje recibido.
9. Publicar un **aviso integral HTTPS** con responsable, domicilio real, contacto atendido, finalidades, consentimiento/retirada, retención efectiva, Kit/GitHub como encargados y transferencias aplicables. Configurar `FCMO_EMAIL_PRIVACY_URL`. El sitio genera el aviso Kit EN/es-419/zh-Hans desde `legal/email-privacy-kit.json`; no reutiliza las promesas de retención de Listmonk. La URL puede ser una página pública administrada por el operador; la home genérica de Kit no es nuestro aviso integral. Con estos requisitos realmente completos, establecer `FCMO_EMAIL_COMPLIANCE_READY=true`.

## GitHub: variables y secretos

En el repositorio: **Settings → Secrets and variables → Actions → Variables → New repository variable**. Para secretos: **Settings → Environments → email → Environment secrets → Add secret**. Restringir `email` a código revisado de `main`; una aprobación requerida por ejecución impediría la operación diaria desatendida.

| Clase | Nombre | Valor / función |
| --- | --- | --- |
| Variable | `FCMO_EMAIL_PROVIDER` | `kit` inicialmente; `listmonk` conserva L26 |
| Variable | `FCMO_EMAIL_ENABLED` | `false` durante preparación; literal `true` para enviar/publicar el alta |
| Variable | `FCMO_EMAIL_COMPLIANCE_READY` | `true` solo con remitente, privacidad y ajustes reales completos |
| Variable | `FCMO_EMAIL_FROM` | Dirección editorial verificada en Kit |
| Variable | `KIT_FORM_EN`, `KIT_FORM_ES`, `KIT_FORM_ZH` | Tres IDs numéricos de formularios |
| Variable | `KIT_TAG_EN`, `KIT_TAG_ES`, `KIT_TAG_ZH` | Tres IDs distintos de etiquetas de producción |
| Variable | `FCMO_EMAIL_PRIVACY_URL` | URL pública HTTPS del aviso integral, sin query, credenciales ni fragmento |
| Variable | `FCMO_EMAIL_BACKUP_AGE_RECIPIENT` | Clave pública age, generada fuera de GitHub |
| Secret `email` | `KIT_API_KEY` | API key v4, solo jobs de correo/backup |
| Secret `email` | `FCMO_EMAIL_POSTAL_ADDRESS` | Dirección postal real para el HTML enviado |
| Variables de prueba | `KIT_TEST_TAG_EN`, `KIT_TEST_TAG_ES`, `KIT_TEST_TAG_ZH` | Tres etiquetas privadas que contienen únicamente al seed confirmado |
| Variable de prueba | `KIT_TEST_SUBSCRIBER_ID` | ID numérico de tu propio perfil confirmado en Kit |

Kit no necesita `FCMO_EMAIL_PUBLIC_URL`, token del gateway, SMTP, SES ni un servidor expuesto. Al seleccionar Listmonk se vuelven a usar las variables/secrets de L26. Su exportación desde Actions requiere credenciales de lectura Listmonk y conectividad privada a su API; no se abre la API pública para conseguir un backup. El backup cifrado del host es la alternativa existente.

Generar una identidad age en la estación privada con `age-keygen -o /private/diario-age-identity.txt`. Guardar esa identidad bajo custodia separada; copiar **solo** la clave pública a la variable. No copiar stdout de identidades/exports al informe. Lanzar **Actions → Encrypted Diario audience backup → Run workflow** y comprobar descifrado, conteos y estados privadamente antes de depender del backup.

## Primera edición de prueba: únicamente a ti

1. Mantener las etiquetas de producción vacías y no promocionar aún los formularios. Suscribirte tú mediante un formulario y confirmar el correo. En **Grow → Subscribers**, abrir tu perfil confirmado y anotar su ID.
2. Crear tres etiquetas privadas `diario-test-en/es/zh` y añadir **solo tu perfil confirmado** a las tres. Establecer `KIT_TEST_TAG_*` y `KIT_TEST_SUBSCRIBER_ID`. El adaptador comprueba que cada etiqueta contiene exactamente ese único suscriptor activo antes del POST. Una variable de etiqueta de prueba ausente no cae en la etiqueta de producción.
3. Después de la revisión/merge/publicación que hará el operador, asegurar una edición LKG **fresca del día**, con noticias nuevas y todos los idiomas. Poner el switch en `true` durante la prueba: el master switch también manda en modo test. Las etiquetas de producción vacías impiden que los disparos programados alcancen lectores durante esta preparación.
4. **Actions → Dispatch FCMO AI Diario → Run workflow → branch main → test_mode marcado → Run workflow**. Este modo envía las tres versiones solo al seed, con namespace `fcmo-diario-test` e intents separados. Repetir el workflow: debe crear **cero broadcasts nuevos**. No usa la clave de producción de esa fecha. Si la edición es QUIET/DELAYED, vieja, incompleta o anterior a las 07:30 CDMX, se omite: no fabricar un receipt ni eludir frescura para probar.
5. Leer los tres mensajes realmente recibidos, confirmar idioma/links/HTML, texto alternativo generado por Kit, autenticación, baja de cuerpo y cabeceras de un clic. Probar unsubscribe y comprobar que el perfil suprimido no vuelve a recibir. Volver a confirmar únicamente si quieres seguir como seed. `QUEUED` por sí solo no satisface estas comprobaciones.
6. Conservar evidencia privada de los supuestos API siguientes. Publicar Pages con los formularios reales configurados, comprobarlos a 390/1440 en EN/ES/ZH y probar alta pendiente/confirmación/baja. Mantener `test_mode` desmarcado para producción. Después, las notificaciones de deploy y ventanas diarias de reintento envían automáticamente; nadie pulsa Send en Kit. Verificar varios días consecutivos y sus backups antes de declarar funcionamiento autónomo real.

## Shapes Kit asumidos: Claude debe confirmarlos en vivo

No hay grabaciones de una cuenta real ni docs descargadas en L27. El servidor [mock_kit.py](tests/harness/mock_kit.py) es una fixture sintética de los shapes v4 solicitados, contrastable con la [referencia pública de Kit](https://developers.kit.com/api-reference/overview). Los enlaces son puntos de continuación, no prueba de navegación en esta sesión.

| Operación | Supuesto exacto probado localmente |
| --- | --- |
| Autenticación | Base `https://api.kit.com/v4`, header `X-Kit-Api-Key`, JSON; no redirect con credenciales |
| Alta estática | POST urlencoded a `https://app.kit.com/forms/<id>/subscriptions`, campo `email_address`; Kit confirma/baja, el formulario asigna la etiqueta mediante configuración |
| Listado | `GET /broadcasts?per_page=100&after=<cursor>` devuelve `broadcasts` y `pagination` con boolean `has_next_page` y string/null `end_cursor` |
| Identidad del broadcast | El listado incluye `id`, `description`, `send_at`, `public`, `subscriber_filter`; descripción persistente/exacta, incluso tras enviar. Si devuelve summaries incompletos, agregar GET del detalle **en el adaptador** y repetir pruebas |
| Creación/envío | `POST /broadcasts`: `subject`, `content` (HTML completo), `description`, `email_address` verificado, `public=false`, `subscriber_filter={"all":[{"type":"tag","ids":[<id>]}]}`, `send_at` ISO UTC actual; respuesta `{ "broadcast": { ... } }` con ID numérico y campos anteriores |
| Contenido/baja | Kit acepta el HTML sin requerir otro layout y resuelve `{{ unsubscribe_url }}` en un href del body; añade o genera texto alternativo/footer/cabeceras de baja adecuados. L27 prueba el HTML previo a Kit, no su MIME final |
| Health | `GET /tags` devuelve `tags` con IDs numéricos y la misma paginación; comprobar etiquetas no prueba permiso de enviar broadcasts |
| Audiencia | `GET /subscribers?status=<estado>` admite active/inactive/bounced/complained/cancelled; `subscribers` incluye `id`, `email_address`, `state`, `fields`, `created_at` y paginación |
| Idiomas/seed | `GET /tags/<id>/subscribers` devuelve membresías de todos los estados; con `status=active` devuelve solo activos y `state=active`. El backup depende de que los suprimidos/pendientes no desaparezcan de las membresías exportadas |
| Errores/consistencia | 429/5xx se pueden reconciliar con lecturas; un broadcast creado acaba apareciendo por su descripción. Si no aparece, el intent bloquea, no autoriza un POST nuevo |

Confirmar primero permiso de API del plan gratuito, payload/filtro y semántica de `send_at` (incluido un timestamp ligeramente pasado durante la petición). Después confirmar opt-in pendiente excluido, tags/form mapping, campos del listado/detalle, baja/supresión, estados/export y paginación. Si hay contradicción, corregir el adaptador y fixtures a la evidencia real; nunca quitar el filtro para que el endpoint responda verde.

## Evidencia y límites de aceptación

Red-first registrado en [red-first.txt](reports/email-kit/red-first.txt) y commit de contratos `e03e70e`. El fallo inicial es la ausencia de `Edition`/API de proveedores. Los logs publicados normalizan las rutas de máquina. La suite incluye contrato de los tres adaptadores, idempotencia tras reiniciar, filtros por locale, switch apagado sin cliente, native ZH incompleto antes del primer request, GET 429/503 acotado, POST perdido/ausente, restauración de intents de otra ejecución, redirect de artefacto sin token GitHub, export de supresión/idioma y cifrado/descifrado real con age. Una exportación fallida no deja archivo. El test aislado no consume claves de producción y rechaza etiquetas con dos lectores.

**Resultado final:** correo **52/52**; suite completa **644 tests, OK, 3 skips** en 130,739 s (un skip histórico y dos por navegador ausente); publicación **13/13**; release de L26 **7/7**; agent hygiene **PASS**; estructura de formularios renderizados **3/3**; YAML, sintaxis Node y `git diff --check` **PASS**. Los resultados están en [reports/email-kit/](reports/email-kit/). **Las comprobaciones de navegador no pudieron ejecutarse:** no existe Playwright/Chromium instalado y la prohibición de red impide descargarlos. No se cambiaron los skips/gates ni se declaró aprobación visual. El oracle se intentó y reportó `BROWSER_UNAVAILABLE`. El binario Listmonk usado en L26 tampoco está disponible aquí; sus receipts anteriores se conservan como evidencia de L26, no como una nueva ejecución nativa de L27. Claude debe repetir ambos límites fuera de esta caja antes de integrar.

Reproducción local / continuación preparada:

```sh
python3 -m unittest discover -s tests -p 'test_email*py'
python3 -m unittest discover -s tests
FCMO_EMAIL_PROVIDER=kit FCMO_EMAIL_ENABLED=true FCMO_EMAIL_COMPLIANCE_READY=true \
  KIT_FORM_EN=101 KIT_FORM_ES=102 KIT_FORM_ZH=103 \
  FCMO_EMAIL_PRIVACY_URL=https://example.org/complete-notice \
  python3 tools/paper/build.py --stories site/data/stories.v2.json \
  --status site/data/newsroom-status.json --out /tmp/l27-proof/publish \
  --base /FCMO-AI-Newsletter/
cp i18n/glossary.yml /tmp/l27-proof/publish/data/glossary.json
python3 tools/gates/run_all.py /tmp/l27-proof/publish
python3 tools/validate_agent_hygiene.py --site /tmp/l27-proof/publish
python3 tools/verify_release.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  python3 tests/oraculos/verificar_paper.py /tmp/l27-proof/publish
FCMO_EMAIL_PROVIDER=kit KIT_FORM_EN=101 KIT_FORM_ES=102 KIT_FORM_ZH=103 \
  PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  node ops/email/review_preview.cjs reports/email-preview /tmp/l27-proof/publish
python3 ops/email/offline_e2e.py --listmonk /path/to/verified/listmonk \
  --pg-bin /usr/lib/postgresql/17/bin
```

Los IDs/domicilios de prueba son sintéticos, no datos de activación. Revisar las capturas finales de los formularios y los emails de L26; el nuevo modo del oracle comprueba la acción Kit y `email_address` y conserva los checks Listmonk. La estructura HTML renderizada se mide por separado; no sustituye mediciones de overflow, tipografía ni consola en un navegador.

Rollback: `FCMO_EMAIL_ENABLED=false`, redeploy de Pages para quitar el alta, mantener backups, audience y journals. La copia puede seguir programada. No se pueden retirar correos ya enviados. Si un intent tiene resultado desconocido, comparar con Kit y evidencia privada antes de cualquier intervención; no borrar artefactos/renombrar campañas para forzar envío. Cambiar de proveedor entre días y conservar suppressions según [EMAIL-PROVIDERS.md](docs/EMAIL-PROVIDERS.md).

**Resumen:** Kit y Listmonk quedan reemplazables por configuración; el envío diario y el backup cifrado están implementados y probados localmente. Faltan navegador, confirmación del plan/API de Kit, configuración real y varios ciclos de entrega autónoma. No se envió correo real ni se hizo push.
