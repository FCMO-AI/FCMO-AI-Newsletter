# Traducción de Studio

El autor elige inglés o español y publica
su texto con versiones fieles en los otros dos idiomas. Esta entrada humana de Studio
es independiente del corpus ARB y de su original canónico inglés. No hay
traducción al abrir páginas ni dentro del build público.

`STUDIO_TRANSLATION_PROVIDER=codex-cli` es el valor predeterminado. Ejecuta
`codex exec`, sin herramientas ni persistencia de sesión, en un
directorio privado vacío y con sandbox de solo lectura. `STUDIO_TRANSLATION_MODEL`
elige el modelo; por defecto es `gpt-6.1-sol`. `STUDIO_TRANSLATION_TIMEOUT=120`
limita la ejecución (1–300 segundos). El host debe tener Codex CLI autenticado
por suscripción. Se hereda solo el entorno necesario para la CLI, sin llaves de
API ni credenciales de publicación. Antes de pedir una traducción, se comprueba
que `codex login status` indique autenticación con ChatGPT; una llave de API
almacenada o un estado desconocido provocan rechazo. No hay alternativa automática de pago por API.
Los documentos son datos, nunca instrucciones; el prompt prohíbe añadidos,
resúmenes y cambios de voz, registro, nombres, citas o marca.

Entrada: `fcmo-studio-translation-request-v1`, con `source` (documento en o es-419),
los otros dos idiomas como `targets`, `rules` y `glossary`. Ejemplo desde español,
con salida estricta y sin Markdown:

```json
{"schema":"fcmo-studio-translation-v1","docs":{"en":{},"zh-Hans":{}}}
```

Cada valor de `docs` es un documento completo `fcmo-essay-doc-v1`.
`glossary.json` fija términos y nombres; los nombres editoriales adicionales
pueden incorporarse allí. Las citas originales (`lang`, citas de bloque y
texto entre comillas) permanecen exactas. Los localizadores de citas pueden
cambiar de idioma conservando sus cifras. Las cifras y fechas conservan sus
tokens originales. Se verifican también títulos, introducciones, recuadros,
notas y enlaces dentro de las notas. Los dos resultados se guardan juntos sólo
si pasan, con conflicto de revisión y locks comprobados otra vez después de la
llamada. El reemplazo exige confirmación y conserva un checkpoint.

`STUDIO_TRANSLATION_PROVIDER=fake` sirve exclusivamente para pruebas de
estructura: su texto no demuestra calidad lingüística. `zdr` reserva la interfaz
`generate(request)` y rehúsa ejecutar; no realiza llamadas de red.

La validación determinista comprueba estructura, términos protegidos y límites
amplios de longitud; no prueba por sí sola equivalencia literaria. Los estados
visibles son `MACHINE_TRANSLATED`, `MACHINE_REVIEWED` y `HUMAN_REVIEWED`.
`MACHINE_REVIEWED` significa que las comprobaciones automáticas pasaron y están
ligadas a los documentos y etiquetas de figuras actuales mediante hashes. Nunca
afirma revisión humana. Editar una etiqueta elimina la revisión vigente;
publicación y correo comprueban también esas etiquetas.
La traducción conserva `origin: agent_draft`; una edición humana pasa a
`agent_draft_human_edited` y vuelve a requerir comprobaciones.

Antes de pedir revisión, Studio genera ediciones faltantes o desactualizadas y
verifica las ediciones editadas. También traduce textos alternativos, pies de
figura y notas de corrección desde un solo original. Los cambios del original
invalidan las otras ediciones; los locks y la revisión evitan sobrescribir
trabajo concurrente. La aprobación editorial revisa el original y autoriza
publicar; conserva revisión humana falsa en los otros idiomas, salvo revisión
de idioma explícita. El validador público repite los controles sin proveedor.

## Correo: interfaz para L28b

`piece.json` admite opcionalmente `distribution: {"email": true|false}`. Las
piezas antiguas sin el campo conservan su validez; Studio activa el envío por
defecto en cartas y ensayos nuevos. El autor puede cambiarlo antes de pedir
revisión; el cambio incrementa la revisión y queda en la misma pieza aprobada.
Studio no envía correo. El dispatcher consume esa intención después del deploy verificado.

Hook integrado L29: `Publisher.public_status` lee por Contents API
`email-dispatch-state:dispatch.json` sólo tras comprobar la publicación web.
`studio.server.distribution.email_status(state, piece_id, requested)` valida la
proyección `fcmo-piece-email-state-v1` de L28b y exige reservas de producción e
ID/programación confirmados en los tres idiomas para mostrar «Correo programado ✓».
Una programación confirmada no demuestra entrega. Registros ausentes, parciales,
inválidos, de prueba o inciertos permanecen pendientes. No se actualiza main, no
se contamina el snapshot de publicación y no hace falta otro deploy. Las claves
son de por vida por pieza/idioma; una enmienda no reenvía la pieza.

La intención aprobada vive en `piece.json` y llega intacta al build público.
`tools/email_dispatch.py --pieces` conecta el CLI común con el dispatcher L28b;
`--collect`, `--claim` y `--send` mantienen prueba LKG, reservas duraderas y
revalidación inmediatamente antes de programar. Studio sólo lee el estado;
el workflow de correo es quien programa y persiste las observaciones.
