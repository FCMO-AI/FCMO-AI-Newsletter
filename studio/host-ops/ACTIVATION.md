# Activación operativa de Studio — L23b

La prueba local usa dos identidades ficticias y un origin bare desechable. No activa
GitHub, Pages, ACL, unidades ni credenciales de producción. El arquitecto realiza
estos pasos después de integrar y revisar `c5/studio-live`.

1. Reemplazar **todas** las apariciones de `@REPLACE_WITH_JAVIER` y
   `@REPLACE_WITH_MATIAS` en `.github/CODEOWNERS` por los handles reales. Ambos
   deben tener permiso **write** en `FCMO-AI/FCMO-AI-Newsletter`. Integrar ese cambio
   antes de activar el ruleset. `publish-gate` corre para todos los PR a main;
   filtrar por paths impediría completar los PR de configuración.
2. Preparar un checkout integrado y ubicaciones privadas fuera de él para datos,
   backups, configuración de gh y recibo del ruleset. Directorios 0700; archivo
   privado de entorno 0600. Copiar `studio/host-ops/studio.env.example`, completar
   `STUDIO_REPO`, `STUDIO_DATA`, `STUDIO_BACKUPS`, `STUDIO_ORIGIN` (HTTPS tailnet),
   clave de sesión aleatoria de al menos 32 caracteres y las dos carpetas gh.
   Mantener `STUDIO_DRY_RUN=1`, `STUDIO_LIVE_ENABLED=0`,
   `STUDIO_ALLOW_NON_EN_SOURCE=0`. No guardar secretos en el repositorio.

   Para una instalación nueva, elegir primero el origen HTTPS privado y crear el
   archivo sin sobrescribir uno existente ni imprimir la clave:

   ```sh
   export STUDIO_ENV_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/fcmo-studio/studio.env"
   export STUDIO_BROWSER_DEPS="${XDG_DATA_HOME:-$HOME/.local/share}/fcmo-studio/browser"
   export STUDIO_RULESET_STATE="${XDG_STATE_HOME:-$HOME/.local/state}/fcmo-studio/main-ruleset.json"
   export STUDIO_ADMIN_GH_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/fcmo-studio/gh-admin"
   : "${STUDIO_HTTPS_ORIGIN:?Definir el origen HTTPS privado de Studio}"
   python3 - <<'PY'
   import os, secrets, shlex
   from pathlib import Path
   target = Path(os.environ['STUDIO_ENV_FILE'])
   private = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'fcmo-studio'
   config = target.parent
   for directory in (config, private, private / 'data', private / 'backups'):
       directory.mkdir(parents=True, exist_ok=True, mode=0o700)
       directory.chmod(0o700)
   browser = Path(os.environ['STUDIO_BROWSER_DEPS']) / 'node_modules'
   values = {
       'STUDIO_REPO': str(Path.cwd()), 'STUDIO_DATA': str(private / 'data'),
       'STUDIO_BACKUPS': str(private / 'backups'),
       'STUDIO_ORIGIN': os.environ['STUDIO_HTTPS_ORIGIN'],
       'STUDIO_SESSION_KEY': secrets.token_urlsafe(48),
       'STUDIO_BIND': '127.0.0.1', 'STUDIO_PORT': '8447',
       'STUDIO_LIVE_ENABLED': '0', 'STUDIO_DRY_RUN': '1',
       'STUDIO_ALLOW_NON_EN_SOURCE': '0',
       'STUDIO_GH_CONFIG_JAVIER': str(config / 'gh-javier'),
       'STUDIO_GH_CONFIG_MATIAS': str(config / 'gh-matias'),
       'PLAYWRIGHT_MODULE': str(browser / 'playwright'),
       'NODE_PATH': str(browser), 'AXE_CORE_PATH': str(browser / 'axe-core/axe.min.js'),
   }
   fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
   with os.fdopen(fd, 'w') as stream:
       stream.write(''.join(k + '=' + shlex.quote(v) + '\n' for k, v in values.items()))
   PY
   ```

   La cuenta administrativa se autentica aparte con
   `GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" gh auth login --hostname github.com`.
3. Instalar `git`, `gh`, Python y Node; instalar navegador en una carpeta privada
   del operador. Estas descargas son preparación, no parte del dogfood sin red:

   ```sh
   npm install --prefix "$STUDIO_BROWSER_DEPS" --no-save playwright@1.63.0 axe-core@4.14.0
   "$STUDIO_BROWSER_DEPS/node_modules/.bin/playwright" install --with-deps chromium
   export PLAYWRIGHT_MODULE="$STUDIO_BROWSER_DEPS/node_modules/playwright"
   export NODE_PATH="$STUDIO_BROWSER_DEPS/node_modules"
   export AXE_CORE_PATH="$STUDIO_BROWSER_DEPS/node_modules/axe-core/axe.min.js"
   ```

   Persistir `PLAYWRIGHT_MODULE`, `NODE_PATH` y `AXE_CORE_PATH` en el entorno
   privado del servicio; la suite usa también los fixtures positivos de axe.
   El bundle de Studio ya está compilado y versionado;
   editar frontend exige `npm ci && npm run build` en `studio/web`.
4. Cargar el entorno privado y autenticar **cada persona** en su configuración,
   sin copiar una cuenta a la otra. No ejecutar estos comandos dentro del log de
   una sesión de agente. Login interactivo; Studio nunca extrae el token de gh:

   ```sh
   set -a; . "$STUDIO_ENV_FILE"; set +a
   GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh auth login --hostname github.com --git-protocol https
   GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh auth login --hostname github.com --git-protocol https
   GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh api user --jq .login
   GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh api user --jq .login
   ```

   Los dos logins deben ser distintos y corresponder a los code owners. Alternativa:
   PAT personales fine-grained en `GH_TOKEN_JAVIER` / `GH_TOKEN_MATIAS` dentro del
   entorno privado, restringidos a este repo: Contents **read/write**, Pull requests
   **read/write**, Actions **read**; Actions **write** para quien solicite rollback.
   Metadata read es implícito. Ninguno puede tener bypass. La cuenta administrativa
   para configurar reglas es separada y necesita Administration **write**.
5. Resolver primero la compatibilidad con el desk autónomo: `newswire-bridge.yml`
   y `daily-refresh.yml` hoy hacen `git push origin HEAD:main` (líneas 506 y 215).
   Un ruleset con PR + otra aprobación y cero bypass **rechazará esos push**.
   No activar las reglas hasta que el arquitecto/operador resuelva este circuito
   conservando la autoridad de publicación y la frescura diaria. Pasar el desk a
   PRs con aprobación humana introduce intervención diaria; se pidió decisión al
   operador, sin cambiar estos workflows ni fabricar otra credencial o bypass.
   Conservar el script listo para inspección/reversión no implica autorizar una
   regresión de la autonomía de v4.

   Inspeccionar JSON y activar las reglas con esa credencial administrativa.
   Conservar el recibo privado; el script guarda intención antes de escribir y
   comprueba el estado recibido. No repetir a ciegas una respuesta incierta:

   ```sh
   sh ops/studio/protect-main.sh --dry-run
   GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" sh ops/studio/protect-main.sh --state "$STUDIO_RULESET_STATE"
   ```

   Con cada cuenta publicadora, comprobar también la visibilidad de la lista
   de excepciones (obtener `STUDIO_RULESET_ID` del recibo privado):

   ```sh
   GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh api "repos/FCMO-AI/FCMO-AI-Newsletter/rulesets/$STUDIO_RULESET_ID" --jq '{enforcement,bypass_actors}'
   GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh api "repos/FCMO-AI/FCMO-AI-Newsletter/rulesets/$STUDIO_RULESET_ID" --jq '{enforcement,bypass_actors}'
   ```

   Debe verse `active` y `[]`, en ambas cuentas y para cada ruleset efectivo.
   Si la lista está oculta/null, Studio rehúsa; no la trata como cero excepciones.
   La API sólo muestra esa propiedad con visibilidad de escritura del ruleset:
   [documentación GitHub](https://docs.github.com/en/rest/repos/rules#get-a-repository-ruleset).
   El arquitecto debe resolver esa visibilidad sin añadir bypass ni sustituir
   la credencial de una publicación al recibir rechazo.

   Exige 1 aprobación de otra persona, code-owner review, descartar revisiones
   obsoletas, aprobación del último push, resolver comentarios, `publish-gate`
   estricto y **cero bypass**. Conserva otros rulesets. Reversal del ruleset:

   ```sh
   GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" sh ops/studio/protect-main.sh --rollback --dry-run --state "$STUDIO_RULESET_STATE"
   GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" sh ops/studio/protect-main.sh --rollback --state "$STUDIO_RULESET_STATE"
   ```

   Si alguien cambió las reglas después del apply, rollback rehúsa sobrescribirlas.
6. Crear los dos usuarios de Studio (contraseñas solicitadas interactivamente) y
   arrancar en modo privado sin publicación. El launcher lee `STUDIO_ENV_FILE`:

   ```sh
   sh studio/host-ops/start.sh --add-user javier
   sh studio/host-ops/start.sh --add-user matias
   sh studio/host-ops/start.sh
   ```

   Escucha exclusivamente `127.0.0.1:8447`; `STUDIO_PORT` sólo cambia el puerto.
   Configurar HTTPS **Tailscale Serve** al listener, sin Funnel; ACL sólo para los
   autorizados y prueba real de acceso de Javier desde su teléfono. Probar health,
   rechazo 401 sin sesión y las dos cuentas. Seguir `RUNBOOK.md` para instalar las
   unidades de usuario y sus drop-ins de entorno/rutas privadas.
7. Ejecutar el ensayo de backup antes del primer uso, instalar el timer horario
   sólo después de que pase y repetir restore mensualmente. Repetir QA local:

   ```sh
   bash studio/host-ops/backup.sh --drill "$STUDIO_DRILL_DEST"
   sh studio/dogfood/run.sh --browser --keep "$STUDIO_DOGFOOD_EVIDENCE"
   python3 ops/publish.py --check
   ```

   El dogfood no usa credenciales reales ni red; sí requiere Chromium ya instalado.
   Incluye `[[`, soltar una foto sobre la página, reordenar tarjetas arrastrando
   y salir de un diálogo de recuperación sin perder el buffer local.
   Genera `summary.json`, logs, frames y main reconstruido en la carpeta elegida,
   que debe estar vacía y fuera del repo. El chequeo estricto ejecuta suite Python,
   los siete controles de release existentes, higiene, 14 gates y navegador. No
   correr dos builds sobre el mismo `publish/` simultáneamente. `--fixture-build`
   se reserva a fixtures internos y nunca autoriza publicación.
8. Javier escribe 1500 palabras, nota/fuente/figura, reabre desde el teléfono y
   verifica que no perdió nada. Marcar los tres idiomas revisados (chino exige
   comprensión explícita), preview, pedir revisión y aprobación de Matías.
   En dry-run el worker conserva la aprobación sin avanzar. Dejar únicamente
   ese candidato aprobado; parar el servidor antes del preflight por CLI:

   ```sh
   python3 -m studio.server.publish --slug "$STUDIO_SLUG" --dry-run
   ```

   Repetir aceptación ≤10 minutos con las dos personas, restore ≤3 clics y revisión
   visual de los frames por los jueces designados. Los agentes de esta tarea no
   representan a esos jueces ni a las dos personas.
9. Cuando las pruebas privadas, credenciales y protecciones estén aceptadas,
   cambiar **en el archivo privado** `STUDIO_DRY_RUN=0`, `STUDIO_LIVE_ENABLED=1` y
   reiniciar `sh studio/host-ops/start.sh` o la unidad instalada. Se reanuda el
   candidato aprobado: PR del autor, revisión del otro, gate, merge fijado,
   Pages del mismo SHA y lectura real de tres URLs con identidad correcta.
   Sólo el estado `published` confirma visibilidad; `deployed_unverified` requiere
   inspección y conserva la frontera. Verificar también la portada real y su
   freshness actual/anterior; una carta nueva no demuestra la operación diaria
   del desk automático. Nunca habilitar originales no ingleses sin decisión Q2.

Recuperación del sitio: botón «Volver a la última versión comprobada», con la frase
exacta. Es una petición de deploy de LKG, no una garantía instantánea ni borrado
retroactivo de lectores. La corrección/retiro permanente sigue el review de ambos.
Restauración privada: `python3 -m studio.server.backup --restore "$STUDIO_SNAPSHOT"
--destination "$STUDIO_NEW_DATA"`; primero parar el servicio y usar un destino nuevo.
