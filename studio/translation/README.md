# Traducción de Studio

Decisión editorial del 5 de octubre de 2026: Javier escribe en español y publica
su texto con versiones fieles en inglés y chino. Esta entrada humana de Studio
es independiente del corpus ARB y de su original canónico inglés. No hay
traducción al abrir páginas ni dentro del build público.

`STUDIO_TRANSLATION_PROVIDER=claude-cli` es el valor predeterminado. Ejecuta
`claude -p --model sonnet`, sin herramientas ni persistencia de sesión, en un
directorio privado vacío. `STUDIO_TRANSLATION_TIMEOUT=120` limita la ejecución
(1–300 segundos). El host debe tener Claude CLI autenticado. Credenciales de
GitHub, Ghost y configuración de Studio se excluyen del entorno del proceso.
Los documentos son datos, nunca instrucciones; el prompt prohíbe añadidos,
resúmenes y cambios de voz, registro, nombres, citas o marca.

Entrada: `fcmo-studio-translation-request-v1`, con `source` (documento es-419),
`targets: ["en", "zh-Hans"]`, `rules` y `glossary`. Salida estricta, sin Markdown:

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

La validación determinista comprueba estructura y términos protegidos; no prueba
por sí sola equivalencia literaria. La revisión humana decide fidelidad semántica,
voz y registro. Los resultados son `agent_draft`, con modelo y revisión falsa;
una edición pasa a `agent_draft_human_edited`, conservando el modelo. Javier puede
marcar cada idioma revisado; la aprobación de Matías revisa todos los idiomas
listos y registra su nombre y fecha sin cambiar quién preparó el texto.

## Correo: interfaz para L28b

`piece.json` admite opcionalmente `distribution: {"email": true|false}`. Las
piezas antiguas sin el campo conservan su validez; Studio activa el envío por
defecto en cartas y ensayos nuevos. El autor puede cambiarlo antes de pedir
revisión; el cambio incrementa la revisión y queda en la misma pieza aprobada.
Studio no envía correo. L28b consume esa intención después del deploy verificado.

Hook de lectura: `studio.server.distribution.email_status(repo_root, piece_id,
merge_sha, requested)`. Recibo en el snapshot público local:
`ops/email-dispatch/pieces/<piece_id>.json`:

```json
{
  "schema": "fcmo-piece-email-dispatch-v1",
  "piece_id": "FCMO-P-0123456789ab",
  "merge_sha": "<40 hex del merge desplegado y verificado>",
  "state": "sent",
  "sent_at": "<UTC RFC3339>",
  "dispatch_id": "<identidad confirmada por el proveedor>"
}
```

L28b debe escribir ese recibo sólo después de confirmar el envío; nunca incluye
suscriptores, direcciones ni credenciales. Studio exige coincidencia de pieza y
merge, además de identidad y fecha no vacías, antes de mostrar «Enviado por
correo ✓». Un recibo ausente, inválido, antiguo o incierto sigue pendiente.
`Publisher.public_status` lee del `store.public_root` (snapshot público del
repositorio). Al integrar L28b, actualizar ese snapshot mediante el mecanismo
existente `studio.server.snapshot.refresh` después de incorporar el recibo;
la función de lectura no hace fetch ni efectos externos. El estado de correo
permanece independiente de «Publicado». Esta lane deja el hook exacto; la
producción del recibo y su refresco posterior pertenecen a L28b.
