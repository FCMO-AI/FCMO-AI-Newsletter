# L23b — Studio, de construido a publicable

2026-10-05 UTC · `c5/studio-live` · Codex · entrega local, sin push.

## Resultado y frontera

La especificación vinculante y la integración montadas fueron leídas y contrastadas
con la implementación. La matriz completa está en
`reports/STUDIO-CONFORMITY-L23b.md`: **111 filas; 95 met, 16 partly met, 0 missing**.
`met` representa implementación y prueba local; las filas parciales conservan la
aceptación humana, acceso tailnet, cuentas/protecciones y publicación real pendientes.
El worker de modelos es la lane C, explícitamente posterior y no bloqueante de v1;
no se afirma que esté instalado ni que sus traducciones tengan aprobación humana.

Se integraron los 19 commits de `origin/main` `a8cfcbb` mediante **`7c202f5`**,
incluido PR #56. Se conservó `REPORT.md` de main en el único conflicto. El chrome,
datos y reglas de freshness v4 ganan; el builder mantiene la entrada editorial de
Studio. No se hizo fetch, push, merge remoto, deploy ni instalación de producción.

**No activar todavía las nuevas protecciones en producción:** los workflows
`newswire-bridge.yml:506` y `daily-refresh.yml:215` hacen push directo a main. PR,
otra aprobación y cero bypass rechazarían esas escrituras. Se pidió decisión al
operador sobre ese circuito; no se cambió el desk ni se inventó una credencial,
aprobación o bypass. El arquitecto debe resolverlo preservando publicación legítima,
autonomía y frescura, antes de aplicar el script. Un Studio local correcto no prueba
la operación diaria ni la freshness del periódico live.

## Trabajo incorporado

- `ops/publish.py --check` ejecuta la suite completa, los siete controles de release
  existentes, exige LKG, reconstruye Story/status/editorial, higiene, **14 gates** y
  el navegador real. `--fixture-build` es explícito y exclusivo de fixtures; no es
  una validación de publicación. El workflow `publish-gate` corre en todo PR a main,
  instala Chromium/Playwright/axe antes del chequeo y conserva permisos read-only.
- El recibo immutable del newsroom se calcula sobre su entrada Story/status y
  editorial vacío explícito. Las piezas humanas se versionan por separado y el
  build combinado sigue sujeto a PIECE_VALID, privacidad, 14 gates y navegador.
  Esto permite una segunda publicación humana sin invalidar el recibo del desk.
- El arranque repara únicamente un origin sin URL; no sustituye una URL incorrecta.
  El launcher obliga loopback y acepta `STUDIO_PORT` alternativo. El estado HTTP de
  publicación se puede leer durante una comprobación larga; ya no espera su mutex.
- Asistencia por párrafo: aceptar, editar y descartar; original presente en el job;
  título/dek, revisión de citas y QA visual determinista sin worker. La aceptación
  mantiene `agent_draft`/`agent_draft_human_edited` y nunca inventa human-reviewed.
- UI de correcciones fechadas, retiro con motivo y notas trilingües, recuperación
  explícita, biblioteca por fecha/tema/clase, edición de issues y comparación de
  dos checkpoints. El atajo `[[` abre la fuente. Se puede soltar una foto en la página y reordenar tarjetas.
- La imagen de canvas se normaliza a WebP sin ICC/EXIF/XMP antes de subir; el servidor
  conserva el rechazo estricto de metadata. La serialización conserva la forma del
  documento, evitando invalidar traducciones al editar sólo metadata de una figura.
- Revisión móvil: elegir un párrafo en el preview, comentar ese bloque y su idioma,
  volver desde el comentario. El renderer compartido conserva ids en todos los
  bloques, no sólo encabezados. Una pieza nueva no pide un diff publicado inexistente.
- `.github/CODEOWNERS` contiene placeholders señalados para ambos handles reales.
  `ops/studio/protect-main.sh` imprime JSON con `--dry-run`, aplica/lee el ruleset,
  guarda intención antes del efecto y permite `--rollback` del estado anterior.
  No sobrescribe reglas modificadas después. Exige una aprobación, code owner,
  last-push, stale dismissal, publish-gate estricto y cero bypass. Studio rehúsa
  también un campo bypass oculto: ausencia no demuestra lista vacía.
- Un fallo de checker conserva sólo identificadores de tests/gates y exit code en
  un diagnóstico privado 0600; nunca trazas, texto de borrador, secretos o rutas.

## Fallos encontrados antes del operador

El dogfood real encontró el bloqueo del GET de progreso durante checks largos,
una URL origin ausente al primer arranque, fixtures que heredaban piezas humanas
y tests que asumían un `_audit` preexistente en un checkout nuevo. Se corrigieron
sus causas y se conservaron las aserciones y gates. El navegador encontró pérdida
de letras en notas, metadata ICC de canvas y desalineación entre forma del documento
y traducciones; tienen pruebas de regresión. La revisión encontró comentarios
siempre al primer bloque y un diff 404 normal tratado como error de consola. La inspección de frames
descubrió que un diálogo de recuperación sobrevivía al cambio de pantalla y tapaba
la revisión. Se cierra al salir y conserva el buffer privado; una regresión de
navegador lo prueba y los 68 frames se repitieron sobre la interfaz corregida.

El selector nativo tuvo fallos intermitentes bajo automatización. El harness ahora
registra la interceptación antes de escribir, conservándola hasta terminar; cinco
recorridos consecutivos pasaron. La aplicación mantiene un único input nativo,
lo limpia tras seleccionar y lo destruye al cerrar el editor. No se sustituyó el
chooser por una inserción artificial ni se silenciaron errores del navegador.

## Evidencia final

Resultados completados, con logs privados en `_audit/studio-l23b/`:

- **Dogfood 23/23, completed=true**, guardado sin rutas ni datos privados en
  `reports/STUDIO-DOGFOOD-L23b.json`. Dos autores publican por HTTP y el build de
  main sirve las tres URLs; los tres rechazos pedidos y rollback real local pasan.
- **Suite completa: 693 tests, 303.202 s, OK; un skip inapplicable** del negativo
  para un renderer ausente. Ningún oracle de refresh/navegador fue omitido.
- Siete controles de release existentes, higiene y **14/14 gates** verdes; **531
  rutas** del input actual. Browser del periódico: 129 stories, tres portadas,
  177 páginas con headings chinos y dos viewports. Cada uno de los cuatro candidatos
  del dogfood ejecutó también la suite/checker estrictos antes del transporte;
  ambos candidatos publicados pasaron PIECE_VALID y navegador con la pieza incluida.
- Web **9/9**; editor final **12/12** (incluye `[[`, foto, offline, drop/reorder y
  diálogo de recuperación); comentarios móviles **4/4**; cierre de diálogo y buffer
  **3/3**; interfaz final axe/overflow **36/36**. La corrección tardía del atajo y del
  diálogo se verificó sobre el launcher real en un segundo store aislado, después
  del bloque de navegador del recorrido principal; no altera su transporte HTTP.
- Ensayo publicado: axe **6/6** y overflow **6/6**, tres idiomas por dos viewports.
  **68 frames** del recorrido, repetidos como **68 frames corregidos** tras el fix
  de diálogo. Inspeccionados traducción móvil, edición, revisión móvil oscura y
  lectura china. No reemplazan a los jueces Sonnet/Opus ni a los dos usuarios reales.
- Regresiones finales de publicación/storage **22 tests** y snapshot/asistencia/
  integración/preview **16 tests** verdes (el mismo skip inapplicable); workflow
  verificado tras fijar la misma versión ejecutada: Playwright 1.63.0 / axe 4.14.0.
- JSON de reglas, apply/restauración previa y create/delete rollback con drift refusal
  pasan sin GitHub real. Bundle íntegro, shell syntax, compilación y diff whitespace
  pasan. No se ha instalado el servicio ni activado protecciones remotamente.

La prueba reproducible está en `studio/dogfood/run.sh` y requiere navegador instalado.

```sh
sh studio/dogfood/run.sh --browser --keep "$STUDIO_DOGFOOD_EVIDENCE"
python3 ops/publish.py --check
npm test --prefix studio/web
sh ops/studio/protect-main.sh --dry-run
```

El dogfood usa el launcher real, dos sesiones HTTP distintas, un Git bare como
origin y fake gh. El transporte/merge, las comprobaciones de candidatos, la
reconstrucción de main y los HTML servidos son reales locales; GitHub, CI y Pages
son control-plane doubles. El fake check también reconstruye un checkout limpio;
no es una respuesta verde sin build. La prueba cubre ambos autores, autorrevisión,
protecciones ausentes, main cambiado, rollback de LKG sin mover main y ausencia de
ramas draft o piezas no aprobadas. El LKG del fixture se fija al commit inicial;
no modela la promoción de LKG que hace Pages después de un deploy bueno. La
recuperación de producción usa el LKG vigente, que puede incluir la pieza nueva.
Con `--browser` añade editor/offline, drop/reorder,
comentarios móviles, traducción, checklist, accesibilidad, frames, acciones y QA.
El resumen tiene denominador fijo **23**, cuenta ejecutada y `completed`; una
interrupción nunca puede producir un 4/4 que parezca una prueba completa.

## Continuación operativa exacta

`studio/host-ops/ACTIVATION.md` contiene los pasos y comandos de principio a fin:

1. Sustituir ambos placeholders por Javier/Matías reales con permiso write e
   integrar CODEOWNERS; mantener `publish-gate` en todos los PR a main.
2. Preparar entorno privado 0600 y directorios 0700; credenciales separadas para
   cada persona, sin mostrarlas al agente. Contents RW, Pull requests RW y Actions
   read; Actions write para rollback. Administrador separado para configurar reglas.
3. Resolver compatibilidad del desk autónomo; inspeccionar dry-run, aplicar reglas
   con recibo privado y comprobar la visibilidad de cero bypass desde ambas cuentas.
4. Instalar navegador/runtime, usuarios, HTTPS tailnet sin Funnel y ACL; arrancar
   en `STUDIO_DRY_RUN=1`, `STUDIO_LIVE_ENABLED=0`. Ensayar backup/restore y timer.
5. Hacer aceptación real de Javier/Matías: 1500 palabras, teléfono sin pérdida,
   revisión trilingüe, restore ≤3 clics, ciclo ≤10 minutos y jueces visuales nombrados.
   Parar Studio y ejecutar `python3 -m studio.server.publish --slug "$STUDIO_SLUG"
   --dry-run`; resolver cualquier rechazo sin sustituir credenciales.
6. Sólo tras aceptar esas fronteras, habilitar live en el archivo privado, reiniciar
   y comprobar PR/review/check/merge/Pages del mismo SHA y las tres URLs. Verificar
   también portada y freshness actual/anterior; `published` exige lectura real.

```sh
sh ops/studio/protect-main.sh --dry-run
GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" sh ops/studio/protect-main.sh --state "$STUDIO_RULESET_STATE"
GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" sh ops/studio/protect-main.sh --rollback --dry-run --state "$STUDIO_RULESET_STATE"
GH_CONFIG_DIR="$STUDIO_ADMIN_GH_CONFIG" sh ops/studio/protect-main.sh --rollback --state "$STUDIO_RULESET_STATE"
sh studio/host-ops/start.sh --add-user javier
sh studio/host-ops/start.sh --add-user matias
sh studio/host-ops/start.sh
```

Los dos logins gh interactivos, variables exactas y preflights están en ACTIVATION.
Una dispatch de rollback pide restaurar LKG; no demuestra serving, no mueve main
y no borra lo visto por lectores. Corrección/retiro permanente conserva dos personas.
