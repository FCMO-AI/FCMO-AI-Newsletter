# Activación operativa de Studio — L25

La secuencia ejecutable y los rollbacks están en [REPORT-L25.md](../../REPORT-L25.md).
Sustituye la guía L23b: handles definitivos, plan de protección y artefactos de
hosting preparados; la activación real sigue pendiente.
No requiere una tercera cuenta ni otro login administrativo. La aceptación real
del bypass de Actions **no está demostrada**: hay un rechazo de esa integración
en una organización documentado en el informe. Si GitHub lo rechaza, mantener
Studio en dry-run y los workflows sin cambios. El fallback de PR por paths no
está expresado por la API de branch rulesets; CODEOWNERS solo no bloquea pushes.

- Javier: `javo-27`; Matías: `Magyarmex`. Ambos administran el repositorio y son
  code owners de `editorial/`, Studio, sus operaciones, workflows y CODEOWNERS.
- `protect-main.sh --dry-run` no necesita red ni credenciales. Exige PR,
  una aprobación de otra persona, code-owner review cuando cambian sus rutas,
  stale dismissal, aprobación del último push, resolución de comentarios y
  `publish-gate` estricto. La única excepción es GitHub Actions
  (`actor_id=15368`, `Integration`, `always`); ningún humano/admin tiene bypass.
  La autonomía requiere probar aceptación y push real con `GITHUB_TOKEN`; un
  JSON y un fake gh no la prueban. Un ruleset de branch
  exige PR en toda main; CODEOWNERS limita la revisión de propietarios a sus
  rutas. No se añaden code owners a los datos del bot.
- Las protecciones efectivas se verifican antes del merge. Una excepción
  humana, otra integración, lista oculta o regla inactiva rechaza la publicación.
  El script conserva otros rulesets y un recibo privado; no repite efectos
  inciertos ni restaura reglas que alguien cambió después del apply.
- Las dos configuraciones gh se guardan en las carpetas privadas acordadas,
  resueltas por `studio.server.credentials.CREDENTIAL_ROOT`, bajo el directorio
  de secretos del host. Cada carpeta es 0700, propiedad de `fcmo-agent`. Los dos
  logins son interactivos y los ejecuta el operador. No hay cuenta compartida,
  extracción de tokens ni fallback a credenciales ambientales.
- `prepare_host.py --origin "$STUDIO_HTTPS_ORIGIN"` crea entorno privado 0600,
  clave aleatoria y datos/backups 0700. Elige mediante `ss -ltn` un puerto libre
  entre 8490 y 8499; el seleccionado en L25 es **8490**. Se vuelve
  a comprobar antes de instalar. No sobrescribe secretos existentes.
- `install.sh` instala `fcmo-studio.service` en `~/.config/systemd/user/`, hace
  `daemon-reload` y `enable --now`. Guarda el estado anterior para `rollback.sh`.
  Ejecutar como `fcmo-agent`, sin sudo. La unidad usa UMask 0077 y
  NoNewPrivileges; el launcher fuerza exclusivamente `127.0.0.1`.
- Studio abre aun sin los logins gh. Después del login local, la interfaz indica
  «Falta iniciar sesión de Javier» y/o «Falta iniciar sesión de Matías». Se puede
  escribir; publicar requiere las dos cuentas. El estado se comprueba cada 30 s.
  Health no divulga datos y la API exige sesión.
- El arquitecto expone después el listener por HTTPS privado en el tailnet,
  nunca Funnel ni `0.0.0.0`. Cookies Secure requieren HTTPS. Probar el teléfono
  de Javier y ACL antes de habilitar publicación.

Mantener `STUDIO_DRY_RUN=1`, `STUDIO_LIVE_ENABLED=0` hasta completar credenciales,
protecciones, backup/restore, QA y aceptación privada con las dos personas.
No habilitar originales no ingleses. Inglés sigue siendo la fuente semántica;
es-419 y zh-Hans conservan sus gates y aprobación explícita.

Sólo Pages publica; `published` exige comprobar tres URLs del merge exacto.
Una pieza humana no demuestra freshness ni ciclos autónomos repetidos del diario.
La prueba local usa origin bare y dos identidades ficticias; no prueba GitHub real.
