# L28a — Español original, traducciones y distribución

2026-10-06 UTC · branch `c5/studio-translate` · entrega local, sin push.

## Resultado y frontera

Javier crea ensayos en español por defecto y ya no necesita una bandera para
usarlo como original. En Idiomas, «Traducir a inglés y chino» guarda los dos
borradores juntos, alineados con el original. Reemplazar traducciones exige
confirmación y conserva una versión anterior. Cambiar el original durante la
llamada provoca conflicto; no sobrescribe el trabajo nuevo.

El proveedor predeterminado ejecuta `claude -p --model sonnet`, con entrada y
salida JSON estrictas, timeout configurable, sin shell, herramientas ni sesión
persistente. Sólo recibe el documento de esa pieza y el glosario; el proceso
excluye credenciales GitHub/Ghost y configuración de Studio. `fake` sirve a las
pruebas; `zdr` es una interfaz que rehúsa ejecutar y no hace llamadas de red.
**Claude no se ejecutó en esta verificación.**

Los controles comprueban ids y orden de bloques, tipos, notas y sus referencias,
citas y localizadores numéricos, figuras, enlaces —también dentro de notas—,
cifras, fechas y ausencia de párrafos vacíos. Protegen citas exactas y términos
del glosario, incluidos nombres y marca; detectan además nombres compuestos del
original español. Un error conserva los documentos anteriores y bloquea la
publicación con una razón en español. Estos controles no prueban equivalencia
literaria ni reconocimiento exhaustivo de nombres: el contrato del proveedor y
la revisión humana cubren significado, registro, voz y nombres no catalogados.

Cada resultado registra `agent_draft` y modelo; una edición registra
`agent_draft_human_edited` y conserva el modelo. Marcar un idioma revisado es una
acción del autor. La aprobación de Matías registra su revisión de los idiomas
listos sin atribuirle su escritura. Pedir revisión privada puede tener esas
marcas pendientes; publicar exige revisión humana y aprobación de la otra
persona. Para las piezas de Javier con original español se exigen EN/ES/ZH
listos. El gate público ya no admite un `agent_draft` sin revisión.

El checklist muestra sitio EN/ES/ZH, RSS/Atom/JSON y correo bajo «Umbral FCMO».
«Enviar por correo a los suscriptores» está activo por defecto para cartas y
ensayos nuevos, y guarda `distribution.email` en la pieza, con revisión de
concurrencia y permisos del autor. El schema v1 mantiene válido el contenido
histórico sin ese campo y rechaza valores o campos adicionales inválidos.
`PIECE_VALID` repite los controles de traducción y revisión. El cambio mínimo en
`tools/paper/essays.py` permite conservar `agent_draft` tras una revisión humana
real; se mantiene el requisito de un revisor identificado.

Studio no envía correo. El hook exacto para L28b está en
[studio/translation/README.md](studio/translation/README.md): recibo
`ops/email-dispatch/pieces/<piece_id>.json`, schema
`fcmo-piece-email-dispatch-v1`, identidad de pieza y merge coincidentes, estado
`sent`, fecha e identidad de despacho. Sólo entonces aparece «Enviado por
correo ✓». L28b debe producirlo tras deploy verificado y refrescar el snapshot
público de Studio; el código de email y sus workflows no se modificaron.

## Evidencia local

- Red-first: `aa9d841`, nueve pruebas con nueve errores antes de implementar.
- Pruebas finales específicas: **12/12**, con HTTP autenticado real, renderer de
  producción, parity, nota omitida, conflictos, procedencia, aprobación de
  Matías, configuración fallida, schema de correo y recibo de despacho.
- Integración existente de Studio: **16/16**, HTTP y git reales con GitHub ficticio.
- Suite completa final, invocada por `python3 ops/publish.py --check`:
  **709 tests, 576.221 s, OK (4 skipped)**. El checker final pasó integridad,
  higiene y los 14 gates, y terminó con **exit 2** exclusivamente al llegar al
  oráculo: `BROWSER_UNAVAILABLE` (Playwright no disponible).
- Web: **9/9**; bundle reconstruido y vinculado a las fuentes por su manifest.
- Build del periódico: **531 rutas**; **14/14 gates** e higiene verdes.
  `PIECE_VALID` también se ejercitó con fixtures publicados y defectos; el build
  de producción actual no contiene piezas humanas.
- Integridad de release: **7/7**.
- Dogfood offline estricto: **6/17**, no completado. Arranque, autenticación,
  escritura sin gh y rechazo de autoaprobación pasan. El candidato fue rechazado
  por el checker local (exit 2, sin tests ni gates fallidos registrados).
  El oráculo directo declara `BROWSER_UNAVAILABLE`: falta Playwright.

Los logs privados están en `_audit/studio-l28a/`. Las cuatro omisiones de la suite corresponden a dos pruebas de Playwright,
una de axe-core y el negativo del renderer ausente (ya integrado). Este entorno
tampoco tiene Chromium ni axe-core. Se reutilizaron paquetes locales ya instalados para
reconstruir Studio sin red; no se modificó ninguna otra worktree. No se omitió
el navegador del checker ni se cambió un gate para obtener verde. **La aceptación
visual y el dogfood completo siguen pendientes**: no hay capturas inspeccionadas,
publicación real, deploy ni envío de correo demostrados en esta lane.

## Continuación

En un entorno con Playwright, Chromium y axe-core disponibles, configurar sus
rutas mediante `PLAYWRIGHT_MODULE`, `CHROME_PATH` y `AXE_CORE_PATH`/`NODE_PATH`, y
repetir sin excepciones:

```sh
python3 -m unittest discover -s tests
npm --prefix studio/web test
python3 ops/publish.py --check
sh studio/dogfood/run.sh --browser --keep _audit/studio-l28a-browser
```

Inspeccionar las capturas de Studio a 390/1440 px, incluidos Idiomas y Publicar.
La fidelidad lingüística real debe probarse con Sonnet y revisión humana del
texto, fuera del fake. La lane L28b conecta su recibo al hook de correo descrito.
No habilitar publicación hasta cerrar las fronteras de hosting, credenciales y
protección remota ya documentadas en REPORT-L25.md.

**Resumen:** traducción ES→EN/ZH, revisión humana obligatoria y correo opcional
implementados y probados localmente. Falta el navegador para cerrar la aceptación
visual y el dogfood completo; no se hizo push ni se publicó.
