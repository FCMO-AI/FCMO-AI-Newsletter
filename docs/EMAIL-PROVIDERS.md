# FCMO AI Newsletter: interfaz de proveedores y migración

La Newsletter de FCMO AI usa `FCMO_EMAIL_PROVIDER=kit` inicialmente. `brevo` ofrece una alternativa alojada de menor costo; `listmonk` conserva la ruta de L26 con gateway, journal SQLite y SES; `fake` sirve únicamente para pruebas locales. Las Cartas de Javier mantienen su ruta editorial independiente.

Un adaptador vive en `tools/email_providers/<nombre>.py`. El selector importa ese módulo por configuración: no hay que cambiar el despachador, el generador ni el exportador. El módulo expone `Adapter`, `public_form(env, locale)` y `PRIVACY_NOTICE` (nombre de un aviso curado en `legal/`). La clase implementa `subscribe_form`, `send_edition(edition, locale, idempotency_key)`, `list_subscribers` y `health`. `public_form` no instancia clientes autenticados. El sitio recibe solo configuración pública; `FCMO_EMAIL_PUBLIC_CONFIG` permite configuración pública adicional de futuros adaptadores. `FCMO_EMAIL_PROVIDER_CONFIG`, secret exclusivo de los jobs de correo, permite pasar configuración privada adicional sin editar los workflows; el adaptador define y valida su formato. Kit y Listmonk usan las variables/secrets explícitos descritos en REPORT-L27.md.

`send_edition` devuelve `QUEUED` cuando se observa la campaña programada y `SKIP` si ya existe. No promete entrega ni llegada a la bandeja. Debe rechazar una clave ajena a la edición/idioma y conservar idempotencia entre procesos y ejecuciones. Un proveedor que necesita el journal de Actions declara `requires_intent = True`; el workflow restaura los intents de ese día y sube el nuevo snapshot antes de enviar. El snapshot contiene solamente claves de edición, nunca direcciones. Si un POST puede haber ocurrido y no se encuentra su campaña, se bloquea la recreación. La concurrencia del workflow y el bloqueo local serializan el envío. No borrar intents/campañas ni cambiar claves para forzar un reintento.

`FCMO_EMAIL_ENABLED=false` desactiva los envíos y los formularios publicados. El build de Pages pasa este valor explícitamente. Las copias siguen funcionando aunque el envío esté apagado. El despachador exige además la edición del día, el horario de L26, material nuevo, los mismos IDs con contenido nativo completo en EN/es-419/zh-Hans y el receipt del candidato LKG verificado en producción. No genera traducciones. Kit usa la descripción `fcmo-diario:<fecha>:<locale>` y tags distintos por idioma alimentados por los formularios activos; el modo de prueba usa `fcmo-diario-test` y artefactos separados. Esos marcadores técnicos se conservan para mantener la idempotencia.

## Copia y recuperación

`backup-email.yml` exporta cada día a las 15:15 UTC. `tools/email_backup.py` escribe JSON directamente a stdin de age. Solo el ciphertext `.age` llega al disco o al artefacto, con retención de 30 días. Los errores de exportación/cifrado eliminan el parcial e impiden subir un backup incompleto. No se imprime ni se guarda el JSON claro. Solo la clave pública age va a GitHub; la identidad de descifrado queda fuera, bajo custodia del operador.

El JSON descifrado usa `schema=fcmo-email-export-v1`, `provider`, `exported_at` y `subscribers`. Cada registro conserva la respuesta del proveedor y agrega `locales`. Kit conserva `id`, `email_address`, `state`, `fields`, `created_at` y cualquier otro campo disponible. Consulta explícitamente los estados active/inactive/bounced/complained/cancelled y las membresías de los tres formularios por defecto (o tags en modo opcional). Listmonk conserva `status`, `lists`, sus estados de suscripción y atributos; `locales` enumera las listas confirmadas. No equiparar los estados de un proveedor a los de otro sin comprobar sus significados.

Para verificar una copia en una estación privada, sin archivo claro:

```sh
age --decrypt --identity /private/age-identity.txt audience.json.age | \
  python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["schema"]=="fcmo-email-export-v1"; print("Backup íntegro:", len(d["subscribers"]), "registros")'
```

No ejecutar ese comando con `set -x`, ni imprimir registros/direcciones. Un backup de audiencia no reemplaza el backup de base de datos/journal de L26, la configuración de formularios/automatizaciones ni las pruebas de consentimiento disponibles en la cuenta.

## Migrar a Listmonk + SES u otro proveedor

1. Poner `FCMO_EMAIL_ENABLED=false` y publicar los formularios desactivados. Esperar a que termine cualquier envío en curso. Descargar el último artefacto cifrado; comprobar fecha, integridad, conteos por estado/idioma y la disponibilidad de evidencia de consentimiento. Conservar la cuenta anterior durante la comprobación.
2. Preparar el nuevo servicio por REPORT-L26.md, o crear un adaptador nuevo bajo el contrato anterior. Configurar confirmación, bajas, supresión, remitente, privacidad y transporte antes de importar.
3. Descifrar por pipe exclusivamente en la estación privada hacia el importador del nuevo proveedor, inicialmente en modo de validación. Mapear `email_address` de Kit a `email` de Listmonk y `locales` a `diario-en`, `diario-es-419`, `diario-zh-Hans`. Conservar los campos del registro original como evidencia privada. Las membresías de locale deben estar verificadas, no inferidas del idioma del correo.
4. Importar como confirmados únicamente los lectores activos cuyo consentimiento/confirmación se pueda demostrar. Mantener bajas, rebotes y quejas bloqueados y fuera de listas enviables; no reactivar cancelled/bounced/complained/blocklisted/unsubscribed. Los pendientes no se convierten en confirmados. Si falta evidencia de consentimiento, resolverla o pedir nueva confirmación por una vía autorizada. Las APIs de importación y formatos CSV son específicos del destino; no hay un importador genérico que prometa conservar estados incompatibles.
5. Comparar conteos y muestras privadas por idioma/estado y probar una baja, una cuenta pendiente, una cuenta suprimida y un seed confirmado. Configurar `FCMO_EMAIL_PROVIDER=listmonk` y los secretos de L26; cambiar también el aviso integral y las variables de formulario. El backup de Actions de Listmonk necesita acceso HTTPS privado/autorizado a su API y credenciales de exportación propias; no exponer `/api` ni ampliar el token del gateway para ello. Si el runner no tiene esa ruta, conservar el backup cifrado del host de L26 o usar un runner con conectividad privada.
6. Cambiar de proveedor entre días de edición, después de reconciliar las campañas del anterior. Los journals de dos proveedores no comparten las campañas: cambiar durante una edición puede reenviarla. Desactivar permanentemente la programación del proveedor anterior, comprobar el nuevo formulario generado y su alta/baja, y reactivar. La siguiente edición nueva debe pasar las mismas comprobaciones LKG y de frescura.
7. Verificar varios ciclos diarios sin intervención, entrega a seeds, bajas y recuperación del backup. Revocar la API key anterior cuando ya no sea necesaria. El ciphertext histórico puede mantenerse hasta su caducidad; nunca subir una lista clara al repositorio, ramas públicas, logs o artefactos.

## L27: configuración por proveedor

Los cuatro módulos son `kit`, `brevo`, `listmonk` y `fake`. El contrato `Provider` y el esquema del backup se conservan; `SubscribeForm.fallback_url` agrega un enlace alojado opcional sin JavaScript. `fake` es exclusivamente de prueba. Cambiar `FCMO_EMAIL_PROVIDER` selecciona también el formulario y el aviso de privacidad del adaptador; no hay que editar Python, HTML ni workflows. Cambiar la variable requiere regenerar/publicar Pages para que el alta y el aviso correspondan al proveedor real. Las variables de build nunca contienen credenciales.

| Proveedor | Configuración pública | Configuración privada de los jobs de correo (secrets del repositorio) |
| --- | --- | --- |
| Kit | Defaults reales en `community/config/kit.json`; overrides `KIT_FORM_EN/ES/ZH` y `KIT_FORM_UID_EN/ES/ZH`; `FCMO_EMAIL_PRIVACY_URL` | Secret de repositorio `KIT_API_KEY`; tags por nombre creados/sincronizados por API; overrides opcionales `KIT_TAG_EN/ES/ZH` |
| Brevo | `FCMO_EMAIL_PUBLIC_CONFIG={"forms":{"en":"https://<cuenta>.sibforms.com/serve/<token-en>","es-419":"https://<cuenta>.sibforms.com/serve/<token-es>","zh-Hans":"https://<cuenta>.sibforms.com/serve/<token-zh>"}}`, `FCMO_EMAIL_PRIVACY_URL` | Secret `FCMO_EMAIL_PROVIDER_CONFIG={"api_key":"<key-v3>","list_ids":{"en":21,"es-419":22,"zh-Hans":23}}`; reemplazar IDs de ejemplo por los reales |
| Listmonk + SES | `FCMO_EMAIL_PUBLIC_URL` y configuración de L26 | Capacidad de dispatch de L26; backup con credenciales Listmonk y conectividad privada |

Todos usan `FCMO_EMAIL_ENABLED`, `FCMO_EMAIL_COMPLIANCE_READY`, remitente verificado `FCMO_EMAIL_FROM`, secret `FCMO_EMAIL_POSTAL_ADDRESS` y clave **pública** `FCMO_EMAIL_BACKUP_AGE_RECIPIENT`. El aviso integral debe identificar al encargado seleccionado y los plazos efectivos antes de activar. Nunca poner `api_key` en `FCMO_EMAIL_PUBLIC_CONFIG`.

Kit filtra por `subscriber_filter=[{"all":[{"type":"tag","ids":[<id-locale>]}]}]`. El probe real del operador (2026-10-05) recibió 422 para filtros de formulario y aceptación/entrega con tags en plan gratuito. Antes del primer envío de cada dispatch y durante el backup diario, se recorren los activos de cada formulario (`GET /forms/<id>/subscribers?status=active`, paginado), se asignan por ID (`POST /tags/<tag>/subscribers/<id>`, 201 inicial/200 repetido) y se verifican en `GET /subscribers/<id>/tags`. Nunca se usa el listado de suscriptores del tag: en la cuenta real tardó minutos en reflejar la asignación. No se usan Rules de Kit. Los tags se resuelven/crean por nombre `newsletter-en`, `newsletter-es-419`, `newsletter-zh-Hans` si no se configuran IDs. Un filtro de formulario queda en el contrato solo para proveedores que lo admitan; Kit rechaza `KIT_FILTER_MODE=form`.

Los defaults no secretos son EN 10007761 / 243b33b9e6, ES 10007787 / 65d33b22fa, ZH 10007798 / 2785dc2091. El embed 10007671 queda sin usar. El formulario POST usa `https://app.kit.com/forms/<id>/subscriptions` con `email_address`; el enlace sin JavaScript usa `https://fcmo-ai.kit.com/<uid>`. Los overrides de ID/uid deben cambiar juntos. `KIT_API_KEY` es secret del repositorio: dispatch y backup no dependen de un environment `email`.

El modo seed usa solo `KIT_TEST_TAG_*` asignados manualmente, nunca sincroniza formularios públicos, y exige que el único activo de **toda la cuenta** sea `KIT_TEST_SUBSCRIBER_ID` con los tres tags verificados por suscriptor. Si ya hay otros activos, falla de forma conservadora. El hook opcional `prepare_edition` del adaptador completa el sync de los tres idiomas antes de crear cualquier broadcast; una llamada directa a `send_edition` sincroniza su idioma. Health verifica formularios y tags explícitos sin crear ni enviar. El backup sync no depende del master switch y conserva los cinco estados globales y de formulario, más tags leídos por suscriptor. El sync es aditivo; no elimina membresías anteriores ni reactiva estados suprimidos.

Para Brevo, crear tres listas y tres formularios alojados con **doble confirmación**: el pendiente nunca debe ingresar a la lista enviable antes del clic. Copiar del HTML público el action `https://<cuenta>.sibforms.com/serve/<token>`; el adaptador usa `EMAIL`, POST urlencoded y consentimiento obligatorio/desmarcado del navegador. No se expone servidor nuestro ni se llama a la API desde el navegador. Confirmar con el formulario real si necesita campos ocultos adicionales, consentimiento con otro nombre o CAPTCHA: esta versión conserva el contrato actual y no supone que el checkbox del navegador sea enforcement de Brevo. Si el HTML real exige campos que no admite esta forma estática, mantener el alta inactiva y corregir exclusivamente el adaptador/presentación según evidencia antes de publicar. No sustituir DOI por `POST /contacts` que active pendientes. La alternativa API `contacts/doubleOptinConfirmation` requeriría un actor privado que reciba el alta; no es la ruta elegida para este sitio estático.

Brevo crea `POST /v3/emailCampaigns` con `name` y `tag` iguales a la clave de edición/locale, `type=classic`, `sender`, `subject`, `htmlContent`, `recipients.listIds` de una sola lista. Después de releer el draft, hace un único `POST /emailCampaigns/<id>/sendNow`. Relee el detalle y acepta `queued`, `inProcess` o `sent` como `QUEUED`/`SKIP`, sin prometer entrega. `{{ unsubscribe }}` debe resolverse en el MIME final. El nombre/tag es una identidad para reconciliar, **no una garantía de unicidad de Brevo**: el intent subido antes de ambas mutaciones y la serialización impiden recreación/envío incierto. Un draft tras un intento desconocido bloquea: no se lo vuelve a enviar automáticamente. Los GET tienen tres intentos acotados; los POST uno. El modo seed específico de Kit se rechaza en Brevo; probar Brevo primero con listas privadas que contengan únicamente seeds confirmados, antes de promover lectores y entre fechas de edición.

**Límite gratuito declarado por el operador: 300 emails/día en toda la cuenta, contactos ilimitados.** La ruta de campañas usa API v3; el acceso efectivo a campañas/create/sendNow del plan y la aplicación del cupo requieren verificación live. No se contrató un plan. `health()` suma `totalSubscribers` de las tres listas y devuelve `status=warning`, `warnings=["brevo_daily_cap_exceeded"]`, `estimated_daily_emails` y `daily_cap=300` cuando la suma supera 300. El preflight lo imprime como warning sin datos personales. Una persona en tres listas cuenta como tres envíos: listas iguales de N lectores implican N×3, de modo que 101×3 ya supera el cupo; 100×3 lo consume entero. Las listas disjuntas se suman, no se multiplican artificialmente. Es una estimación conservadora de la Newsletter, no una consulta de créditos restantes: DOI, pruebas y otros envíos comparten el cupo y pueden hacerlo insuficiente incluso por debajo de 300. El adaptador no divide campañas para eludir el cupo ni compra créditos; no garantiza que Brevo acepte/complete las tres campañas al agotarse. Mantener audiencia y consumo totales dentro del cupo antes de activar; una respuesta de límite o estado desconocido deja el intent para reconciliar.

## Migrar Kit → Brevo y Brevo → Kit desde el export cifrado

Aplicar primero los pasos de pausa, reconciliación, custodia y verificación de la sección anterior. Descargar `.age` y descifrar **por pipe en una estación privada** hacia un importador revisado del proveedor destino, inicialmente en validación. No hay importador genérico en este repositorio ni se promete que las APIs de importación preserven consentimiento. No guardar CSV/JSON claro en repo, runner, artefactos ni logs; no imprimir direcciones. La evidencia de DOI/consentimiento y la configuración de formularios se custodian aparte: el export no inventa datos que el proveedor no entrega.

| Dirección | Campo de correo | Idioma | Estados que requieren tratamiento |
| --- | --- | --- | --- |
| Kit → Brevo | `email_address` → `email` | `locales` de formularios o tags → tres `list_ids` de Brevo | Solo `active` con consentimiento y confirmación comprobables entra a listas enviables. `inactive` sigue pendiente; `cancelled`, `bounced`, `complained` se mantienen suprimidos (`emailBlacklisted` según API/importador real) y fuera de listas enviables. No usar `updateEnabled` para deshacer supresiones existentes |
| Brevo → Kit | `email` → `email_address` | `locales` de `listIds` → tres formularios Kit, o tags con mapping por idioma verificado | `emailBlacklisted=true` permanece suprimido; `false` **no demuestra DOI**. Confirmar atributos/registros de DOI y membresía confirmada antes de activar. Contactos fuera de listas enviables, pendientes y supresiones se conservan como evidencia privada; no crear como active por defecto ni usar la suscripción a formularios para reactivar bajas |

Brevo exporta **todos** los contactos paginados con campos originales: `emailBlacklisted`, `smsBlacklisted` si disponible, `listIds`, `attributes`, `createdAt`, `modifiedAt` y cualquier otro campo retornado. Agrega `locales` sin eliminar el blacklist ni convertir la presencia en una lista en prueba de consentimiento. Kit exporta los cinco estados y membresías de formularios y tags por suscriptor, incluidos pendientes/suprimidos. Si el API real no expone una membresía o estado necesario, el backup no es suficiente para esa migración hasta resolverlo; mantener la copia privada del proveedor original.

En ambos sentidos, comparar conteos por locale/estado, conservar la unión de suppressions del origen y destino, probar baja/pendiente/suprimido/seed y confirmar que ningún pendiente o suprimido recibe una campaña. Cuando el destino no pueda representar una supresión, dejarla fuera de su audiencia y conservar un registro privado de exclusión con enforcement verificado; no activar mientras pueda reingresar automáticamente. No reenviar confirmaciones masivas sin autorización ni asumir que importación equivale a consentimiento. Cambiar el selector y config entre días, regenerar Pages, desactivar permanentemente el envío anterior y reactivar solamente después de verificar remitente, notice, alta DOI, filtros y bajas reales. Si se vuelve a Kit, confirmar que importar una membresía de formulario no reactive ni envíe incentive indebidamente; si el plan/API no soporta esa importación de forma segura, usar tags únicamente si su mapping está disponible o mantener la pausa. Comprobar varios ciclos y descifrado del backup nuevo antes de revocar las credenciales anteriores.

## L28b: cartas, ensayos y notas por correo

`dispatch-pieces.yml` se ejecuta después del workflow de Pages exitoso, con un
reintento programado diario y una entrada manual de prueba. Comparte la
serialización `fcmo-daily-email` con el diario. Con `FCMO_EMAIL_ENABLED` apagado
no lee piezas ni crea el adaptador. No traduce: consume `fcmo-piece-v1`,
`doc.<locale>.json` (`fcmo-essay-doc-v1`), `provenance.json`, `sources.json` y
`figures.json` publicados por el build de Studio.

La selección exige `status=published`, fecha de publicación no futura y
`distribution.email=true` **booleano**. La ausencia del flag significa false.
Por idioma exige `locales.<locale>=ready`, documento presente y
`provenance.<locale>.human_reviewed=true` **booleano**. Un idioma pendiente o
sin revisión se omite con `locale_not_ready` o `human_review_required`; los demás
idiomas revisados pueden salir. Una revisión posterior incorpora únicamente la
clave del idioma que faltaba. Una pieza retirada, un borrador y una distribución
no solicitada no se envían. No existe un corte temporal diario para piezas: una
pieza publicada, solicitada y todavía sin correo es el trabajo pendiente.

Los insumos se descubren con `git ls-tree` del commit inmutable de `lkg`, no del
checkout de main. El recibo live de L27 comprueba la identidad LKG y las rutas
críticas; luego se comparan byte por byte los JSON y figuras públicos contra
ese commit y se comprueban las páginas revisadas en `/cartas/<slug>/`,
`/es/cartas/<slug>/` y `/zh/cartas/<slug>/`. La identidad se relee al terminar y
el conjunto se vuelve a verificar inmediatamente antes de enviar. Si el sitio
cambió o no publica los documentos, falla cerrado. Esta rama no contiene todavía
el build de piezas: requiere integrar el build de Studio antes de despachar
piezas reales. Un LKG sin piezas solicitadas produce una selección vacía.

El renderer conserva párrafos, títulos, listas, citas, lenguaje original de
las citas, evidencia y límites, figuras con crédito/licencia y firma de los
autores. Las notas se numeran por primera referencia y pasan a notas finales
con enlaces y retorno. La composición usa los colores, tabla de 640 px y
tipografía del email diario. `render_piece_email` no requiere Ghost.
`render_letter_email` es un wrapper de datos para previews anteriores;
`ghost_url` queda únicamente como alias de URL obsoleto, sin API ni editor.

Kit y Brevo reutilizan sus mismos adaptadores de creación/reconciliación con
`description=fcmo-piece:<id>:<locale>` en Kit y `name`/`tag` iguales a esa clave
en Brevo. Kit conserva los filtros de **tags**, el sync previo y el rechazo de
filtros de form (422 en el fixture del probe del operador). Los destinos son
los mismos tags/listas de cada idioma que el diario. Un ID confirmado significa
campaña programada/encolada; no acredita entrega ni ubicación en inbox. Se
conservan remitente, dirección postal, baja y gates de compliance de L27.

El modo `test_mode` de Kit usa los mismos `KIT_TEST_TAG_*`, sin fallback de
producción, y exige el único activo de la cuenta con los tres tags revisados
por suscriptor. No hace sync de formularios públicos. Las claves son
`fcmo-piece-test:<id>:<locale>` y los registros van a `dispatch-test.json`,
separados de los de producción. Brevo y Listmonk rechazan ese modo de Kit.

Listmonk admite piezas mediante su API **privada**, con listas públicas de
doble confirmación y el template raw HTML de L26. El gateway público de L26
sigue con su capacidad de diario. Para piezas, usar un runner con ruta privada
autorizada a Listmonk y un secret `FCMO_EMAIL_PROVIDER_CONFIG` con
`LISTMONK_URL`, `LISTMONK_API_USER`, `LISTMONK_API_KEY`,
`FCMO_EMAIL_CONSENT_KEY` (los nombres de L26); remitente, dirección postal y
`FCMO_EMAIL_PUBLIC_URL` vienen de las mismas variables/secrets del workflow.
La clave y el journal protegen create/start inciertos. El adaptador falla
cerrado si sólo dispone de la capacidad del gateway; no expone `/api` ni
amplía su token. No se afirma acceso privado desde un runner hosted.

### Registro público que puede leer Studio

La rama dedicada **`email-dispatch-state`**, archivo **`dispatch.json`**, es la
fuente del estado de producción. No se escribe main ni se necesita otro deploy
para observar el correo. Studio puede leerlo mediante
`GET /repos/<owner>/<repo>/contents/dispatch.json?ref=email-dispatch-state`
(Contents API; decodificar base64), o mediante la URL raw de esa rama.
`dispatch-test.json` es sólo prueba y nunca debe activar el indicador de
producción. El workflow crea la rama desde el commit público LKG cuando no
existe; necesita `contents:write` en su `GITHUB_TOKEN`.

```json
{
  "schema": "fcmo-piece-email-state-v1",
  "provider": "kit",
  "keys": ["fcmo-piece:FCMO-P-123456789abc:es-419"],
  "records": [{
    "piece_id": "FCMO-P-123456789abc",
    "locale": "es-419",
    "state": "QUEUED",
    "broadcast_id": 123,
    "timestamp": "2026-10-06T14:00:00Z"
  }]
}
```

Cada registro contiene exactamente esos cinco campos, sin título, cuerpo,
direcciones, listas de suscriptores, destinatarios ni secretos. Estados:
`PENDING` (reserva duradera), `QUEUED` (ID y programación confirmados),
`SKIPPED_UNREVIEWED`, `SKIPPED_NOT_READY`, `BLOCKED_RECONCILE`. El hook para
«Enviado por correo ✓» es `records` con el mismo `piece_id`, `locale` y
`state=QUEUED`; el detalle debe decir «programado/encolado» y no «entregado».
Un estado previo QUEUED se conserva cuando una revisión posterior omite ese
idioma. Mostrar éxito por pieza completa exige QUEUED en los tres idiomas.

`keys` es el intent permanente sin contenido de L27: se lee antes de reservar
el lote, se guarda **antes de cualquier broadcast**, se confirma por readback
y se sube además un `email-intent.json` con `keys` y `previous`. El intento
local se bloquea y hace fsync antes de cada POST. El estado remoto usa la SHA
del Contents API como precondición y confirma cada escritura; un conflicto o
respuesta incierta bloquea el envío. La rama conserva intents después de
caducar artefactos; no depende de los 90 días del artefacto auxiliar. Nunca
eliminar claves, registros, campañas ni cambiar namespaces para forzar envío.

Una reserva sin campaña observada bloquea recreación, incluso si el workflow
falló entre reserva y upload o antes de la primera llamada. Reconciliar el
proveedor y el intent antes de una recuperación autorizada. Una campaña
existente con el mismo marker y destino confirmado produce SKIP con su ID;
una respuesta de create perdida no provoca otro POST. Cada idioma se intenta
por separado ante un resultado de proveedor incierto, y cada pieza conserva
sus observaciones antes de continuar. Un draft incierto no se vuelve a iniciar.

Cambiar de proveedor requiere reconciliar todas las piezas pendientes además
del diario; el estado detecta y rechaza un cambio de proveedor para impedir
reenviar piezas históricas. Mantener los registros y hacer una migración
explícita después de esa reconciliación. Apagar `FCMO_EMAIL_ENABLED` detiene
nuevos envíos; no revoca campañas ya programadas ni recupera correo entregado.
