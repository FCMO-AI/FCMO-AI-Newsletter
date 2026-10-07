# L23b — Studio publicable: conformidad y prueba real local

2026-10-05 UTC · `c5/studio-live` · merge `7c202f5` de `origin/main` `a8cfcbb`.

Matriz contra STUDIO-SPEC v1 y STUDIO-INT montados. Cada fila agrupa sólo cláusulas que comparten mecanismo y evidencia; las referencias cubren §§1–14, S1–S9, J1–J5 y la integración. `met` afirma implementación/evidencia local; **no convierte GitHub falso en producción real**. Se conserva la autoridad del operador en Q1/Q2/Q5 y la aceptación humana.

**Totales: 111 filas; 95 met, 16 partly met, 0 missing.**

| Spec | Requisito | Estado | Evidencia / frontera |
|---|---|---|---|
| 1.1 | Página de escritura; ensayo, carta y nota sin código | met | `studio/web/src/screen-editor.js:18` |
| 1.2 | Autosave, historia, cursor y restauración sin destruir trabajo | met | `tests/test_studio_storage.py:30` |
| 1.3 | Tres idiomas, estados y revisión deliberada | met | `studio/server/storage.py:223` |
| 1.4 | Un botón, revisión privada, publicación y enlaces live | partly met | `studio/dogfood/run.py:143` — Camino local real; GitHub y Pages de producción esperan credenciales/protecciones. |
| 1.5 | Producción humana sin agentes | met | `tests/test_studio_publish.py:133` |
| 1.6 | Edición curada de piezas y briefs de sólo lectura | met | `studio/web/src/screen-issues.js:8` |
| 1.7 | Loopback, cuenta por persona y acceso sólo tailnet | partly met | `studio/host-ops/start.sh:15` — Loopback probado; HTTPS privado, ACL y acceso de Javier requieren al operador. |
| 1, no objetivos | Sin coedición en tiempo real, scheduling, envío de correo, analítica, comentarios públicos, edición ARB ni bypass | met | `studio/server/http.py:23` |
| 2.1 | Escritura independiente de modelos y llamadas de traducción | met | `studio/web/src/editor.js:15` |
| 2.2 | Un renderer y preview idéntico byte por byte | met | `tests/test_studio_preview.py:13` |
| 2.3 | Documento cerrado, sin HTML almacenado | met | `tests/test_piece_contract.py:22` |
| 2.4 | Ningún borrador remoto antes del acuerdo de ambos | met | `tests/test_studio_publish.py:44` |
| 2.5 | Sin push a main ni sustitución de credencial al rechazo | met | `tests/test_studio_publish.py:83` |
| 2.6 | Publicado exige visibilidad; máquina nunca implica revisión humana | met | `tests/test_studio_publish.py:97` |
| 2.7 | Chrome ES/EN y errores en lenguaje corriente | met | `studio/web/src/i18n.js:2` |
| J1 | Escribir, notas, fuentes, figura, reabrir, traducir, preview, revisar y publicar | partly met | `studio/dogfood/run.py:187` — Automatizado en fixtures; falta aceptación por Javier y tiempo humano ≤10 min. |
| J2 | Matías ensambla y pide revisión de una edición trilingüe | met | `tests/harness/browser/studio_actions.mjs:7` |
| J3 | Errata/aclaración/corrección sustantiva con nota fechada y revisión | met | `studio/web/src/publication-actions.js:5` |
| J4 | Retiro como tombstone; recuperación temporal con límite explícito | met | `studio/web/src/publication-actions.js:29` |
| J5 | Asistencia opcional, marcada, aceptable/editable/descartable por párrafo | met | `studio/web/src/assistant.js:6` |
| S1 | Lista, atención, continuar, estados, palabras, idioma, búsqueda y creación | met | `studio/web/src/screens-home.js:38` |
| S2, página | Columna, título serif, dek, firma, tiempo y estilo de lectura | met | `site-src/assets/css/essay.css:18` |
| S2, bloques | h2/h3, citas, listas, separador, figura, nota, fuente y evidencia por /; atajo [[ | met | `studio/web/src/editor.js:128` |
| S2, selección | B/I/enlace/nota/fuente al seleccionar texto | met | `studio/web/src/editor.js:231` |
| S2, notas | Edición en sitio, margen ≥1100 y notas al final en móvil | met | `studio/web/src/editor.js:77` |
| S2, fuentes | Título, organización, fecha, URL, acceso, localizador y clase opcional | met | `studio/web/src/drawers.js:12` |
| S2, evidencia | Clase, confianza y límites editables | met | `studio/web/src/editor.js:51` |
| S2, drawers | Índice, versiones, fuentes, comentarios y comprobaciones | met | `studio/web/src/screen-editor.js:142` |
| S2, barra/enfoque | Palabras, guardado, idiomas, preview/publicación, foco y scroll | met | `studio/web/src/screen-editor.js:170` |
| S2, conflictos | 409 y elección explícita entre diferencias/local/servidor | met | `studio/web/src/screen-editor.js:110` |
| S2, lock | Un editor por idioma, lectura/comentarios y takeover explícito o tras inactividad | met | `tests/test_studio_storage.py:38` |
| S3 | Columnas alineadas, chips inmutables, origen y cambios del original | met | `tests/harness/browser/studio_translate.mjs:15` |
| S4 | Preview autenticado, tres idiomas, 390/1440 y claro/oscuro | met | `studio/web/src/screens-flow.js:163` |
| S5, contenido | Título/dek/firma, figuras/derechos, notas, citas y enlaces válidos | met | `studio/server/checks.py:5` |
| S5, idiomas | Ready o luego, aviso de máquina y confirmación china | met | `studio/server/storage.py:223` |
| S5, privacidad | Cuatro comprobaciones privadas sobre el preview estricto | met | `studio/server/preview.py:60` |
| S5, publicación | Comprobación completa, destino de errores y otro revisor; aviso de exposición pública | met | `studio/web/src/screens-flow.js:186` |
| S6 | Preview, diff publicado, selección de párrafo por idioma, aprobación y pedir cambios en móvil | met | `tests/harness/browser/studio_review.mjs:21` |
| S7 | Timeline persistido, rechazo y tres URLs observadas | met | `studio/web/src/screens-flow.js:259` |
| S8 | Biblioteca por tipo/fecha/tema/clase, confianza/importancia, slots y nota por idioma | met | `studio/web/src/screen-issues.js:11` |
| S9 | Checkpoints, nombres, comparación entre dos versiones y restore con copia previa | met | `studio/web/src/drawers.js:54` |
| 5.1, árbol | Piezas, fuentes, figuras WebP, provenance y ediciones versionadas | met | `studio/server/storage.py:102` |
| 5.1, contratos | Piece/doc/issue cerrados; ids, URLs, correcciones y retiro | met | `tests/test_piece_contract.py:10` |
| 5.2 | SQLite WAL, worktrees privados, cursor, locks, reviews, audit y estados | met | `studio/server/storage.py:60` |
| 5.3 | Procedencia, revisor/fecha/modelo y revisión humana explícita | met | `tests/test_studio_publishable.py:72` |
| 6, renderer/CSS | Renderer semántico, escaping y contrato de clases compartido | met | `tests/test_essay_build.py:15` |
| 6, discovery | Rutas, shelf/landing, feeds, sitemap, búsqueda y llms | met | `tests/test_essay_build.py:46` |
| 6, pending/retiro | Aviso localizado, original enlazado y tombstone | met | `tests/test_essay_build.py:71` |
| 6, gates | PIECE_VALID y ENGLISH_LEAK preservan privacidad, paridad y citas marcadas | met | `tests/test_piece_gate.py:58` |
| 6, deploy | Editorial activa Pages y validación PR; LKG anterior recuperable | met | `tests/test_studio_live.py:13` |
| 7, runtime | Python stdlib, servidor threaded, SQLite, git sin shell y gh/REST | met | `studio/server/__main__.py:14` |
| 7, configuración | Dos credenciales, secret privado, unidades, port 8447 y publicación protegida | partly met | `studio/host-ops/studio.env.example:3` — Artefactos listos; instalación y cuentas reales no ejecutadas. |
| 7.1, API | API real de documento/recursos/idiomas/historia/comentarios/revisión/asistencia/ediciones | met | `studio/server/http.py:55` |
| 7.1, preview/health | Preview y assets privados; health sin texto y sin autenticación | met | `tests/test_studio_auth.py:39` |
| 7.2, autosave | Escritura atómica fsync/rename, rev y buffer local/reconexión | met | `tests/harness/browser/studio_editor.mjs:77` |
| 7.2, historia | Idle ≥60 s, lock release, nombre, restore y diff por palabras | met | `studio/server/storage.py:241` |
| 7.2, remoto | Restricción studio/*, ninguna rama draft/* ni ancestro privado | met | `tests/test_studio_publish.py:50` |
| 7.3, auth | Scrypt 2^15, cookie Secure/HttpOnly/Strict, 30 días y lockout 5/15 min | met | `tests/test_studio_auth.py:57` |
| 7.3, CSRF/CSP | Origin exacto y token; CSP local sin scripts remotos | met | `tests/test_studio_auth.py:43` |
| 7.3, documentos | Validación PUT y pegado convertido a nodos cerrados | met | `tests/test_studio_auth.py:62` |
| 7.3, figuras | Re-encode y retirada ICC/EXIF/XMP; servidor rechaza metadata y dimensiones inválidas | met | `studio/web/test/webp.test.mjs:5` |
| 7.3, dos personas | Autor de PR y cuenta distinta revisora; sin confiar en identidad tailnet | met | `studio/server/credentials.py:40` |
| 8.1 | Solicitud privada sin transporte; revisión atómica de rev | met | `studio/server/publishing.py:28` |
| 8.2 | Candidate desde main fresco, sólo pieza/issue; suite, siete controles existentes, build, 14 gates y navegador | met | `ops/publish.py:22` |
| 8.3 | Push/PR del autor; sólo refs studio; idiomas y máquina descritos | met | `studio/server/publishing.py:325` |
| 8.4 | APPROVE del otro sobre el último head | met | `studio/server/publishing.py:330` |
| 8.5 | publish-gate actual, timeout 30 min y rechazo de rojo | met | `studio/server/publishing.py:334` |
| 8.6 | Main/head/check/protecciones revalidados; merge por autor, sin bypass | met | `studio/server/publishing.py:340` |
| 8.7 | Pages observado sobre merge SHA y evento push | met | `studio/server/publishing.py:109` |
| 8.8 | HTTP 200 + article id en tres locales; retry 2 min/30 min | met | `studio/server/publishing.py:353` |
| 8.9 | Timeline/audit propios; sin escribir el ledger del desk | met | `studio/server/publishing.py:222` |
| 8, recuperación | Intención antes del efecto; restart/UNKNOWN no reintentan a ciegas | met | `tests/test_studio_publish.py:101` |
| 8, rollback | Dispatch por persona y confirmación; efecto probado sirviendo LKG sin mover main | met | `studio/dogfood/run.py:184` |
| 9, alineación | Source locale, hashes de bloques y regreso a drafting cuando cambia el original | met | `tests/test_studio_storage.py:52` |
| 9, estructura | Paridad de ids/notas/citas/figuras/números/URLs | met | `tests/test_piece_gate.py:28` |
| 9, lectores | Ready humano, aviso de agente sin revisión, pending con enlace original | met | `tests/test_essay_build.py:85` |
| 9, chino | Confirmación explícita leí/entiendo antes de marcar revisado | met | `studio/server/storage.py:226` |
| 9, sin red | Build sin traducción; ES original sigue deshabilitado mientras Q2 no cambie política | met | `studio/host-ops/studio.env.example:13` |
| 10, jobs | Queue/done de la pieza elegida, revisión por párrafo y procedencia sin inventar revisión | met | `studio/server/assist.py:16` |
| 10, clases | translate/cite_check/dek y layout QA determinista en Studio | met | `studio/server/http.py:140` |
| 10, worker ausente | Heartbeat 10 s, no_worker, botón deshabilitado; J1–J4 independientes | met | `tests/test_studio_auth.py:71` |
| 10, privacidad | Sólo el autor pide y lee sugerencias; traducción recibe original, no destino vacío | met | `tests/test_studio_publishable.py:66` |
| 10, worker real | Productor externo de sugerencias opcional | partly met | `studio/server/http.py:143` — Fuera de v1 según lane C; mecanismo y consumo implementados, trabajador real no instalado. |
| 11, tailnet | Serve HTTPS privado, jamás Funnel; acceso Javier | partly met | `studio/host-ops/RUNBOOK.md:30` — Requiere acceso/ACL del operador. |
| 11, backup | Bundle todas las ramas + SQLite + figuras; 0700; 48 horarios + 30 diarios | met | `studio/server/backup.py:43` |
| 11, restore | Integridad, reconstrucción de autosave, accounts, checkpoints y HTTP | met | `tests/test_studio_backup.py:10` |
| 11, operación | Health, restart on failure, backup horario y drill mensual | partly met | `studio/host-ops/fcmo-studio.service:9` — Archivos presentes; unidades/timer no instalados por esta tarea. |
| 12, contratos/build | Fixtures inválidos, render 3 idiomas, discovery, pending, tombstone y gates | met | `tests/test_piece_gate.py:28` |
| 12, servidor | Auth, CSRF, rev/lock, uploads, revisión, selección, fallos y reconciliación | met | `tests/test_studio_publish.py:19` |
| 12, preview/backup | Identidad byte a byte y round-trip del respaldo | met | `tests/test_studio_preview.py:13` |
| 12, UI editor | 300 palabras, nota, fuente, figura, reload/cursor y offline/reconexión | met | `tests/harness/browser/studio_editor.mjs:14` |
| 12, UI traducción/checklist | Cambios de fuente, chips bloqueados y figura sin alt con destino | met | `tests/harness/browser/studio_publish.mjs:18` |
| 12, UI accesibilidad | Axe y overflow de S1–S9 en 390/1440; instrumentación CSP sólo en test | met | `tests/harness/browser/studio_a11y.mjs:16` |
| 12, frames y jueces | Frames S1–S9/ensayo, idiomas, claro/oscuro y juicio Sonnet/Opus | partly met | `tests/harness/browser/studio_frames.mjs:13` — Frames e inspección local; falta la aceptación de los jueces nombrados, no se atribuye a este agente. |
| 12, aceptación humana 1–4 | Javier 1500 palabras, teléfono sin pérdida, misma lectura, restore ≤3 clics y ciclo humano ≤10 min | partly met | `tests/harness/browser/studio_editor.mjs:14` — Automatización apoya la aceptación; Javier/Matías deben hacer el ejercicio real. |
| 12, aceptación 5 | Borrador de máquina nunca aparece como human-reviewed | met | `tests/test_studio_assist.py:11` |
| 12, aceptación 6 | Listener real 8447 y sitio inaccesible fuera de tailnet | partly met | `studio/host-ops/RUNBOOK.md:31` — Listener alternativo probado; falta instalación privada real. |
| 12, aceptación 7 | No draft/* ni slug no aprobado en origin real | partly met | `studio/dogfood/run.py:186` — Demostrado en bare local; repetir contra GitHub con las cuentas reales. |
| 13, integración | Contratos A1, servidor A2 y diseño B conservados; main v4 gana chrome/datos/freshness | met | `tests/test_studio_integration.py:19` |
| 13, M2/operación live | Publicar y verificar periódico real | partly met | `studio/dogfood/run.py:81` — Software y doble local; publicación real queda tras la activación del arquitecto. |
| 14 Q1 | Acceso de Javier al nodo con ACL limitada | partly met | `studio/host-ops/RUNBOOK.md:32` — Decisión y acceso del operador. |
| 14 Q2 | Autorizar originales no ingleses y actualizar LOCALIZATION | partly met | `studio/host-ops/studio.env.example:13` — Se conserva English canonical; requiere decisión explícita del operador. |
| 14 Q3 | Piezas nuevas Studio-native en editorial; Ghost sólo legado | met | `studio/server/storage.py:102` |
| 14 Q4 | Sin excepción de autorrevisión tras 48 h | met | `studio/server/publishing.py:273` |
| 14 Q5 | Ambos code owners con permiso write y dos tokens/accesos | partly met | `./.github/CODEOWNERS:4` — Placeholders deliberados; reemplazo por cuentas reales y acceso de ambos pendiente. |
| INT, merges | A1/A2/B ya integrados; ahora origin/main con 19 commits, incluido #56 | met | `REPORT-STUDIO-INT.md:7` — Merge actual 7c202f5; conflicto sólo REPORT.md, versión main conservada. |
| INT, contrato | UI ligada a endpoints reales, sin API dev en el camino | met | `studio/web/src/api.js:6` |
| INT, suite | Suite completa y preview byte-identity | met | `tests/test_studio_preview.py:13` |
| INT, launcher/HTTP | Servidor por launcher loopback/puerto alternativo y recorrido HTTP con fake gh | met | `studio/dogfood/run.py:128` |
| INT, host | Comandos exactos y aceptación puerto real/navegador/live | partly met | `studio/host-ops/RUNBOOK.md:28` — Comandos actualizados en este informe; efecto externo no ejecutado. |
| INT, entrega | Branch c5/studio-live, commit Codex y no push | met | `studio/dogfood/run.sh:3` — Entrega local; ningún transporte hacia origin real. |
