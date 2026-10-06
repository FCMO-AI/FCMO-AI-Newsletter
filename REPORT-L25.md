# L25 — Activación de Studio

2026-10-05 UTC · entrega local en `c5/studio-live`, sin push.

## Resultado y frontera real

CODEOWNERS tiene `javo-27` y `Magyarmex`. El plan de ruleset propone exclusivamente
GitHub Actions como bypass; Studio acepta esa excepción y sigue rechazando
excepciones humanas, otras integraciones y metadata oculta. Se conservan los
workflows diarios, sus pushes con GITHUB_TOKEN y todos los gates. No se ha
demostrado que GitHub acepte esa excepción en este repositorio.

Se entregan unidad de usuario, preparación privada, instalación con recibo,
rollback y estado de credenciales en la UI. El launcher fue probado en
**127.0.0.1:8490** sin los dos logins gh: health 200, API privada 401 sin sesión,
escritura disponible y ambos avisos visibles a 390 y 1440 px. Las capturas finales
se inspeccionaron; se corrigió un `null` que aparecía en el escritorio vacío.

**No se afirma activación real de systemd, tailnet, ruleset remoto ni publicación
real.** Esta sesión tiene UID `fcmo-agent`, pero no gestor systemd de usuario ni
runtime de logind, no tiene las carpetas de credenciales provisionadas y no dispone
del origen HTTPS privado. `systemctl --user` declara el gestor offline. El
instalador comprueba ese requisito antes de escribir. El arquitecto debe ejecutar
la secuencia siguiente en la sesión de host; los dos logins son del operador.
No se solicitó autorización adicional ni se hizo push.

## Evidencia

Logs y capturas quedan en el área privada `_audit/studio-l25/`; no se publican
datos del host ni credenciales. Resultados comprobados:

- Suite completa: **700 tests, 296.798 s, OK**, un skip inapplicable del negativo
  para el renderer ausente. Ningún gate ni oracle aplicable se omitió.
- Siete controles de release existentes, higiene y **14/14 gates** verdes; build
  actual de **531 rutas**. `verified-check.log` conserva la evidencia completa.
- Web: **9/9**. Arranque sin gh y navegador de credenciales: **6/6**, 390/1440 px,
  listener `127.0.0.1:8490`, dos avisos, sin overflow y sin texto `null`.
- `protect-main.sh --dry-run` offline muestra sólo GitHub Actions, ID 15368.
  Apply/read-back/rollback y conflictos de otras protecciones tienen regresión.
- Unidad verificada por `systemd-analyze --user verify`, exit 0. Como aquí no
  existe runtime de logind, se suministró un directorio temporal 0700 como
  `XDG_RUNTIME_DIR`; esto verifica la unidad, no instala ni arranca un gestor.
- Oracle del periódico: **PASS**, tres locales × dos tamaños; presupuestos de
  layout para 129 stories, tres portadas y 177 páginas con headings chinos.
  `python3 ops/publish.py --check` final terminó con exit 0.
- Dogfood offline con navegador: **25/25**, completado. [Recibo sanitizado](reports/STUDIO-DOGFOOD-L25.json).
  Los cuatro candidatos pasaron individualmente los 700 tests, los 14 gates y
  el oracle de tres locales × dos tamaños. Se probaron rechazo por protección
  ausente, main cambiado antes del transporte y rollback a LKG sin alterar main.

El dogfood emplea git/build/HTTP reales con control GitHub ficticio y origin bare;
no contacta GitHub ni usa cuentas reales. Cada candidato ejecuta el checker
estricto, incluida suite e integridad, antes del transporte local.

La identidad de la integración se comprobó en la API pública de GitHub:
[`github-actions`, App ID 15368](https://api.github.com/apps/github-actions).
El [contrato REST de rulesets](https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset)
documenta bypass `Integration` en modo `always`. Eso **no prueba elegibilidad
del App integrado de Actions**. [Flatcar reportó el rechazo real de la API en una
organización el 2026-07-30](https://github.com/flatcar/Flatcar/issues/2248): el actor
debe pertenecer al origen del ruleset o a la organización. Es evidencia primaria
de otro repositorio, no una respuesta observada en FCMO. La aceptación de 15368
y un push con GITHUB_TOKEN siguen sin verificar aquí. No se declara viable esa
activación por el JSON ni por el fake gh.

El fallback pedido tampoco se puede afirmar implementado: el contrato REST
documentado condiciona los rulesets de branch por referencia, sin una condición
de paths para `pull_request`. `file_path_restriction` bloquea archivos; no crea
revisión PR condicional por ruta dejando otros pushes directos libres. CODEOWNERS
selecciona revisores de PR, pero por sí solo no bloquea pushes humanos directos.
No se sustituyó esto por bypass humano, PAT o App distinta. Si GitHub rechaza
15368, dejar el desk actual sin cambios y mantener Studio en dry-run; no hay una
protección equivalente demostrada bajo las decisiones vigentes. Esta es una
frontera real adicional a hosting/logins, no una decisión que esta lane reabra.

En el plan, el PR aplica a main completa;
la revisión de code owners aplica cuando el PR toca sus rutas. Se exige además
una aprobación general para cualquier PR humano. No hay excepción para admins.
Las reglas se acumulan: el apply rehúsa otras reglas efectivas que bloquearían
Actions y protección clásica incompatible, sin alterarlas. Esos casos tienen
regresión; la aceptación de GitHub real sigue pendiente de apply/read-back.

## Comandos de host, en orden

Usar una shell nueva sin `GH_TOKEN` ni `GITHUB_TOKEN`, para que gh utilice la
configuración personal indicada. Ejecutar desde el checkout integrado, como `fcmo-agent`, salvo los comandos
privilegiados expresamente indicados. Cada bloque incluye su reversión. No
imprimir el entorno privado. Instalar Node, GitHub CLI y Chromium antes del
dogfood offline; no confundir esa preparación con la prueba sin red.

### 1. Arquitecto: comprobar host y provisionar carpetas

```sh
umask 077
export STUDIO_ENV_FILE="$HOME/.config/fcmo-studio/studio.env"
export STUDIO_HOST_STATE="$HOME/.local/state/fcmo-studio"
export STUDIO_BROWSER_DEPS="$HOME/.local/share/fcmo-studio/browser"
export STUDIO_RULESET_STATE="$STUDIO_HOST_STATE/main-ruleset.json"
export STUDIO_CREDENTIAL_ROOT="$(python3 -c 'from studio.server.credentials import CREDENTIAL_ROOT; print(CREDENTIAL_ROOT)')"
id
ss -ltn
systemctl --user show-environment
```

Son consultas/variables; rollback: `unset` de esas variables. Si el gestor de
usuario no está disponible, el arquitecto ejecuta en el host con privilegios:

```sh
mkdir -p "$STUDIO_HOST_STATE"
chmod 700 "$STUDIO_HOST_STATE"
loginctl show-user fcmo-agent --property=Linger --value > "$STUDIO_HOST_STATE/linger.before"
sudo loginctl enable-linger fcmo-agent
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
systemctl --user show-environment
sudo install -d -o fcmo-agent -g fcmo-agent -m 0700 \
  "$STUDIO_CREDENTIAL_ROOT" "$STUDIO_CREDENTIAL_ROOT/javier" "$STUDIO_CREDENTIAL_ROOT/matias"
```

Ejecutar `install -d` también cuando el gestor ya esté disponible. Conservar
carpetas existentes y sus credenciales. Rollback de linger sólo si antes era `no`
y después de parar Studio: `sudo loginctl disable-linger fcmo-agent`; restaurar
las variables previas de la sesión. Rollback de carpetas recién creadas, sólo
vacías: `rmdir "$STUDIO_CREDENTIAL_ROOT/javier" "$STUDIO_CREDENTIAL_ROOT/matias" "$STUDIO_CREDENTIAL_ROOT"`.
Nunca borrar carpetas con logins o borradores para revertir una instalación.

### 2. Arquitecto: origen, entorno y dependencias

Elegir un puerto HTTPS **privado del tailnet** sin configuración Serve existente.
Este ejemplo reserva HTTPS 8490; si ya está usado, elegir otro y conservarlo en
todos los comandos. El listener de Studio se elige independientemente en 8490–8499.
Guardar la configuración previa y resolver el DNS real, sin inventar una URL:

```sh
tailscale serve status --json > "$STUDIO_HOST_STATE/tailnet.before.json"
export STUDIO_TAILNET_HTTPS_PORT=8490
export STUDIO_TAILNET_DNS="$(tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))')"
export STUDIO_HTTPS_ORIGIN="https://$STUDIO_TAILNET_DNS:$STUDIO_TAILNET_HTTPS_PORT"
python3 studio/host-ops/prepare_host.py --origin "$STUDIO_HTTPS_ORIGIN"
npm install --prefix "$STUDIO_BROWSER_DEPS" --no-save playwright@1.63.0 axe-core@4.14.0
"$STUDIO_BROWSER_DEPS/node_modules/.bin/playwright" install chromium
set -a
. "$STUDIO_ENV_FILE"
set +a
ss -H -ltn "sport = :$STUDIO_PORT"
systemd-analyze --user verify studio/host-ops/fcmo-studio.service
```

El `ss` previo a instalación debe quedar vacío. La preparación no sobrescribe
un entorno existente; en una instalación previa inspeccionarlo privadamente y
conservar su copia 0600 antes de ajustar port/origin/credenciales. Rollback de
preparación nueva: parar Studio y renombrar el entorno a `studio.env.disabled`,
conservar datos y backups. Rollback de dependencias nuevas: renombrar sólo
`"$STUDIO_BROWSER_DEPS"` a `"$STUDIO_BROWSER_DEPS.disabled"`; no tocar una instalación
anterior ni cachés compartidas. Queries y verificación no modifican servicio.

### 3. Arquitecto: cuentas locales, servicio y acceso privado

```sh
sh studio/host-ops/start.sh --add-user javier
sh studio/host-ops/start.sh --add-user matias
sh studio/host-ops/install.sh
systemctl --user is-enabled fcmo-studio.service
systemctl --user is-active fcmo-studio.service
ss -ltn "sport = :$STUDIO_PORT"
curl --fail "http://127.0.0.1:$STUDIO_PORT/healthz"
curl -s -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:$STUDIO_PORT/api/pieces"
sudo tailscale serve --bg --https="$STUDIO_TAILNET_HTTPS_PORT" "http://127.0.0.1:$STUDIO_PORT"
tailscale serve status --json
```

Contraseñas locales se piden interactivamente; acordarlas con cada persona por
canal privado. Health debe responder 200; API sin cookie, 401; `ss` debe mostrar
**Local Address = 127.0.0.1**. La dirección comodín de Peer Address no es un bind.
Probar desde el teléfono de Javier las ACL autorizadas y el login HTTPS. Antes
del gh login la UI debe mostrar ambos avisos y permitir escribir. Nunca Funnel.

Rollback del proxy nuevo: `sudo tailscale serve --https="$STUDIO_TAILNET_HTTPS_PORT" off`;
preservar otros puertos/configuración. Rollback del servicio:
`sh studio/host-ops/rollback.sh`; restaura unidad y estados anteriores a partir
del recibo privado. Si alguien modificó la unidad, rehúsa sobrescribirla. Las
cuentas locales y borradores se conservan; el servicio parado impide su acceso.
Los comandos de consulta no requieren rollback.

### 4. Operador: únicamente los dos logins gh, interactivos

Ejecutar fuera de una sesión de agente o log automático:

```sh
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/javier" gh auth login --hostname github.com --git-protocol https
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" gh auth login --hostname github.com --git-protocol https
```

Javier autentica `javo-27`; Matías autentica `Magyarmex`. Nunca compartir una cuenta.
Rollback de cada login:

```sh
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/javier" gh auth logout --hostname github.com --user javo-27
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" gh auth logout --hostname github.com --user Magyarmex
```

El arquitecto comprueba identidad sin extraer tokens:

```sh
test "$(GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/javier" gh api user --jq .login)" = javo-27
test "$(GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" gh api user --jq .login)" = Magyarmex
chmod 700 "$STUDIO_CREDENTIAL_ROOT/javier" "$STUDIO_CREDENTIAL_ROOT/matias"
find "$STUDIO_CREDENTIAL_ROOT" -type f -exec chmod 600 {} +
```

Son comprobaciones y permisos owner-only; no copiar/mostrar tokens. A los 30 s
los avisos deben desaparecer. Un fallo conserva publicación bloqueada y edición
privada disponible. La operación de permisos mantiene el requisito de seguridad;
no tiene reversión a permisos abiertos.

### 5. Arquitecto: probar la aceptación del plan con una cuenta admin

**La elegibilidad de Actions está pendiente y tiene counterevidencia pública.**
El apply siguiente puede ser rechazado por GitHub. Un rechazo no autoriza otro
bypass ni activar PR obligatorio sin excepción, que rompería el desk. CODEOWNERS
debe estar integrado en main antes del apply. Ninguno de estos
comandos hace push. Usar la configuración de Matías, ya admin, sin tercer login:

```sh
sh ops/studio/protect-main.sh --dry-run
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" sh ops/studio/protect-main.sh --state "$STUDIO_RULESET_STATE"
export STUDIO_RULESET_ID="$(python3 -c 'import json,os; print(json.load(open(os.environ["STUDIO_RULESET_STATE"]))["id"])')"
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/javier" gh api "repos/FCMO-AI/FCMO-AI-Newsletter/rulesets/$STUDIO_RULESET_ID" --jq '{enforcement,bypass_actors}'
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" gh api "repos/FCMO-AI/FCMO-AI-Newsletter/rulesets/$STUDIO_RULESET_ID" --jq '{enforcement,bypass_actors}'
```

Continuar sólo si apply/read-back confirman aceptación. Ambas cuentas deben
observar `active` y únicamente App 15368. Si faltan permisos
o la lista queda oculta, corregir esa frontera; Studio no inventa lista vacía.
Si otras reglas bloquean Actions, apply falla antes de mutar y requiere
reconciliarlas conservando su política. Prueba local no sustituye observar un
ciclo diario real tras activación; no afirmar autonomía real hasta ese recibo.

Rollback exacto del ruleset aplicado:

```sh
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" sh ops/studio/protect-main.sh --rollback --dry-run --state "$STUDIO_RULESET_STATE"
GH_CONFIG_DIR="$STUDIO_CREDENTIAL_ROOT/matias" sh ops/studio/protect-main.sh --rollback --state "$STUDIO_RULESET_STATE"
```

Read-back debe confirmar restauración. Un apply incierto exige reconciliar el
recibo y la API antes de repetir; no borrar el recibo para intentar otra vez.

### 6. Arquitecto: aceptación, backup y habilitación

```sh
export STUDIO_DRILL_DEST="$STUDIO_HOST_STATE/restore-drill-l25"
export STUDIO_DOGFOOD_EVIDENCE="$STUDIO_HOST_STATE/dogfood-l25"
bash studio/host-ops/backup.sh --drill "$STUDIO_DRILL_DEST"
sh studio/dogfood/run.sh --browser --keep "$STUDIO_DOGFOOD_EVIDENCE"
python3 ops/publish.py --check
```

Destinos de evidencia vacíos. Son pruebas locales; rollback: conservar evidencia
fuera de la publicación. Un restore-drill no reemplaza datos activos. Instalar
backup horario después de que pase:

```sh
install -m 600 studio/host-ops/fcmo-studio-backup.service "$HOME/.config/systemd/user/"
install -m 600 studio/host-ops/fcmo-studio-backup.timer "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now fcmo-studio-backup.timer
```

En instalación nueva, rollback: `systemctl --user disable --now fcmo-studio-backup.timer`,
quitar únicamente las dos unidades nuevas y `systemctl --user daemon-reload`.
Si ya existían, guardar/restaurar sus archivos y estados en vez de sobrescribirlos.

La habilitación live queda bloqueada si el paso 5 no prueba la política y la
escritura autónoma de Actions. Con ambas personas probar escritura y reapertura móvil, EN/ES/ZH con revisión
explícita, preview, revisión de la otra persona y dry-run. Para preflight CLI,
parar primero el servicio; después volver a arrancarlo:

```sh
systemctl --user stop fcmo-studio.service
python3 -m studio.server.publish --slug "$STUDIO_SLUG" --dry-run
systemctl --user start fcmo-studio.service
```

`STUDIO_SLUG` es el candidato aprobado. Rollback: volver a arrancar el servicio
si el preflight falla, conservando dry-run. No inventar aprobación de idiomas.
Después de completar esa aceptación, habilitar en el archivo privado:

```sh
cp -p "$STUDIO_ENV_FILE" "$STUDIO_HOST_STATE/studio.env.before-live"
python3 - <<'PY'
import os
from pathlib import Path
p = Path(os.environ['STUDIO_ENV_FILE'])
s = p.read_text()
assert 'STUDIO_DRY_RUN=1\n' in s and 'STUDIO_LIVE_ENABLED=0\n' in s
p.write_text(s.replace('STUDIO_DRY_RUN=1\n', 'STUDIO_DRY_RUN=0\n').replace('STUDIO_LIVE_ENABLED=0\n', 'STUDIO_LIVE_ENABLED=1\n'))
p.chmod(0o600)
PY
systemctl --user restart fcmo-studio.service
```

Rollback de flags: `cp -p "$STUDIO_HOST_STATE/studio.env.before-live" "$STUDIO_ENV_FILE"`
y `systemctl --user restart fcmo-studio.service`. Parar/dry-run no despublica un
texto ya enviado. Para compensar publicación, usar retiro revisado y sus notas;
para servir LKG, usar el botón de rollback y esperar prueba real de Pages.
Sólo `published` tras las tres URLs del merge confirma publicación. Verificar
también la portada/freshness y varios ciclos diarios autónomos; siguen siendo
propiedades independientes de esta activación de Studio.

Serve/rollback de proxy siguen la [documentación oficial de Tailscale](https://tailscale.com/docs/reference/tailscale-cli/serve).
Persistencia del gestor usa [loginctl enable-linger](https://www.freedesktop.org/software/systemd/man/252/loginctl.html).
