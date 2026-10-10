# Activar Studio con un idioma de origen

Preparar un checkout limpio del commit aprobado. Conservar el entorno privado,
base de datos, borradores y credenciales fuera del checkout. Hacer una copia de
seguridad antes del cambio y mantener el checkout anterior para volver atrás.

En el checkout nuevo, reconstruir la interfaz con las dependencias ya fijadas:

```sh
cd studio/web
npm ci
npm run test
npm run build
cd ../..
python3 -c 'from studio.server.bundle import ready; assert ready(".")'
```

La reconstrucción es obligatoria: Studio rechaza un bundle cuyo manifiesto no
coincide con sus fuentes. No reiniciar apuntando al checkout nuevo si falla este
paso. No actualizar hashes a mano ni desactivar ese control.

En el archivo de entorno privado del servicio:

```sh
STUDIO_REPO=<checkout-nuevo>
STUDIO_TRANSLATION_PROVIDER=codex-cli
STUDIO_TRANSLATION_MODEL=gpt-6.1-sol
STUDIO_TRANSLATION_TIMEOUT=120
STUDIO_DRY_RUN=1
STUDIO_LIVE_ENABLED=0
```

Codex CLI debe estar instalado y autenticado por suscripción para el usuario que
ejecuta Studio. Comprobar con `codex exec --help` que admite los argumentos de
`CodexCLITranslator.command`. El proceso conserva la autenticación de la CLI,
excluye llaves de API y credenciales de publicación, usa un directorio temporal,
desactiva herramientas y descarta trazas. Modelo y timeout son configurables;
la sesión y sus límites deben estar disponibles. No configurar una llave como
alternativa automática.

Para observar suscripciones desde Studio, configurar el proveedor y su credencial
solo en ese entorno privado. Sin acceso, los conteos se muestran como `?`.
La consulta lee estados y membresías; no suscribe personas ni repara etiquetas.
Los workflows de correo existentes siguen siendo los responsables de programar
ediciones y piezas después de verificar producción.

Con el bundle verificado, ajustar el entorno del servicio y ejecutar:

```sh
systemctl --user restart fcmo-studio
systemctl --user is-active fcmo-studio
```

Comprobar health y sesión por el origen privado configurado. Recorrer a 1440 y
390 píxeles: crear solo en español y solo en inglés; guardar; abrir Publicar;
esperar traducciones; revisar sus estados y editar una; pedir revisión; aprobar
en seco con la otra persona. Modificar el original, comprobar obsolescencia y
regeneración. Hacer una corrección escribiendo solo una nota en el idioma original.
Repetir después de reiniciar y confirmar persistencia.

Configurar en Kit los tres mensajes de doble opt-in y las rutas de retorno:
alta pendiente a `subscribe/check-inbox/`, confirmación a `subscribed/` y baja a
`unsubscribed/`, con el prefijo de idioma correspondiente. Cada mensaje debe
explicar que, si no fue el destinatario quien solicitó el alta, puede ignorarlo,
que solo se envían ediciones después de confirmar y que cada envío permite baja.
Usar «Confirmar mi correo», «Confirm my email» y «确认我的邮箱» en el botón.
Verificar SPF, DKIM, DMARC y la recepción/baja real antes de habilitar correo.

Este procedimiento no autoriza publicación ni envíos reales por sí solo. Conservar
las protecciones, aprobación editorial y verificación de producción existentes.
Para volver atrás, restaurar el checkout anterior en el entorno y reiniciar el
mismo servicio; conservar los datos privados y el historial de correo.
