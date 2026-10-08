# Studio — un URL privado

URL para compartir: **https://fcmo-hub.tail8cbe0b.ts.net:8447/**.
Backend exclusivo: **127.0.0.1:8490**. No se instala el servicio desde esta lane.

Estado 2026-10-08 06:30 CDMX (verificación en el host, fuera del sandbox): el índice de
búsqueda quedó reparado en main (#66, `79055f8`). Con Chromium del host, el recorrido
`tests.harness.studio_host_journey` pasa: 51 comprobaciones y 46 capturas. Studio arrancó
como unidad `--user` transitoria en 127.0.0.1:8490: health 200, HTML y assets 200, APIs y
vista previa 401 sin sesión. Falta que main vuelva a verde (L41): mientras `ops/publish.py
--check` falle en main, Studio rehúsa publicar, y así debe ser.

Una vez preparado el entorno y las dos cuentas locales, ejecutar esta única línea
desde la raíz de este checkout, en la sesión de host de `fcmo-agent` que tenga
el permiso de operador de Tailscale:

```sh
python3 ops/studio/host.py --install && sudo tailscale serve --bg --https=8447 http://127.0.0.1:8490
```

La línea instala [la unidad de usuario](ops/studio/fcmo-studio.service), la arranca
y comprueba health, HTML, JS/CSS actuales y API privada antes de añadir el mapping.
No modifica los mappings 8443–8446. El operador de Tailscale del host es `magya`, no `fcmo-agent`: por eso el
mapping lleva `sudo`. No hay otro bypass de ese permiso.

## Preparación previa

Conservar cualquier entorno, login, borrador o instalación existente. La preparación
no requiere tokens para escribir; publicar requiere las dos identidades personales
y las protecciones ya definidas. Seguir [ACTIVATION.md](studio/host-ops/ACTIVATION.md)
para provisionar las carpetas privadas de gh y el gestor systemd de usuario.

En un host nuevo, con esas carpetas provisionadas:

```sh
python3 studio/host-ops/prepare_host.py --origin https://fcmo-hub.tail8cbe0b.ts.net:8447
export STUDIO_ENV_FILE="$HOME/.config/fcmo-studio/studio.env"
STUDIO_ENV_FILE="$STUDIO_ENV_FILE" sh studio/host-ops/start.sh --add-user javier
STUDIO_ENV_FILE="$STUDIO_ENV_FILE" sh studio/host-ops/start.sh --add-user matias
node studio/web/build.mjs
python3 ops/studio/host.py
```

Las contraseñas se introducen interactivamente, nunca en la línea de activación.
El entorno debe apuntar a este checkout, usar `STUDIO_PORT=8490`,
`STUDIO_BIND=127.0.0.1` y el origen exacto de arriba. `prepare_host.py` puede elegir
otro puerto si 8490 está ocupado; en ese caso resolver la ocupación antes de
ejecutar esta activación. Los datos quedan fuera del checkout, modo 0700; el
entorno y la base de cuentas, modo 0600. No imprimir sus valores privados.

Mantener `STUDIO_DRY_RUN=1` y `STUDIO_LIVE_ENABLED=0` hasta que las credenciales,
protecciones, backup y aceptación de publicación real estén comprobadas. Se puede
crear, guardar, traducir manualmente, previsualizar y revisar en este modo; la
interfaz declara que la publicación pública está desactivada.

## Comprobación del operador

Después de la activación, abrir el URL desde el tailnet, iniciar ambas sesiones y
guardar/recargar un texto. Revisar una vista previa desde el mismo URL en escritorio
y teléfono. Confirmar `systemctl --user is-active fcmo-studio.service` y
`tailscale serve status`: 8447 debe apuntar sólo a 127.0.0.1:8490. No usar Funnel.

La prueba local no demuestra DNS/TLS, ACL, persistencia de systemd ni acceso de
Javier. El operador debe confirmar esas capas antes de declarar el URL live.

Para desactivar únicamente el mapping nuevo: `tailscale serve --https=8447 off`.
Para restaurar la instalación anterior de la unidad:
`sh studio/host-ops/rollback.sh`. No borrar datos ni credenciales. Si la instalación
se interrumpe después de crear su recibo, reconciliar o hacer rollback antes de
reintentar; el instalador conserva ese límite y rehúsa sobrescribir el recibo.
