# Carril studio-un-autor

El autor inicia y completa la publicación sin una segunda cuenta. Se conserva el merge por la API existente y todas las compuertas automáticas. No se crean reviews ni reglas de GitHub. Las publicaciones persistidas en reviewed continúan por los mismos checks. La revisión seleccionada se congela al pulsar Publicar; cambios posteriores se rechazan. La reanudación de un incidente de integridad exige confirmación auditada del autor, con los mismos límites anteriores.

La interfaz pasa de Publicar al progreso; los enlaces antiguos de revisión llevan al flujo actual. Los textos activos describen publicación y verificación. El correo por defecto es false, incluso cuando un fixture habilita el canal; no se cambió la configuración del host ni se envió nada. Los avisos de publicación existentes siguen siendo informativos.

## Evidencia y límites

- Base limpia 44de0d2c0: `python3 -m unittest discover -s tests -p 'test_studio_*.py'`: 274 pruebas, OK, una omisión preexistente (408.479 s), en snapshot local independiente.
- `python3 -m unittest discover -s tests -p 'test_studio_*.py'`: 280 pruebas, OK, 1 omisión preexistente (402.605 s). Antes: 274; después: 280. Sin errores ni fallos.
- `node studio/web/build.mjs`: OK (fallback offline); `node --check studio/web/dist/app.js`: OK; bundle ready=True. `git diff --check` y diff contra base: limpios. `python3 -m compileall -q studio/server studio/dogfood studio/host-ops`: OK.
- Comprobaciones finales posteriores a ajustes de copia/adaptador: `python3 -m unittest tests.test_studio_auth`: 11 OK; `python3 -m unittest tests.test_studio_publish`: 21 OK. El adaptador mantiene también la inyección de fallo previa al efecto de la base.
- Regresiones vistas fallar antes del cambio: `test_author_publishes_without_second_account` (preflight exigía reviewer), `test_author_request_red_gate_blocks` y `test_change_after_publish_is_rejected` (no avanzaban sin otra cuenta). Después pasan.
- Se añaden seis pruebas Python: autor sin otra credencial llega a published; gate rojo público; revisión cambiada; gate local rojo sin efectos; doble clic idempotente; recuperación de estado reviewed antiguo sin credencial del revisor. La batería existente cubre conflictos, replays, checks tardíos, protección, CODEOWNERS, diff, deploy, tres idiomas, correo simulado y HTTP sobre git local.
- JS disponible: 23/23 pasan (controlador Publicar, checks rojos/desconocidos, permisos de reanudación, login, estados, bundle servido y rechazo de drift). `node --test studio/web/test/{author-publish,email-banner-copy,github-card,halt-resume,login,progress-time,webp}.test.mjs` ejecutados como siete argumentos explícitos. No hay prueba de aspecto final en Chromium.
- `node --test studio/web/test/*.test.mjs`: 23 pasan y un archivo falla al cargar docmodel.test.mjs: falta prosemirror-model ya declarado. No se instalaron dependencias. El compilador offline existente se amplió para regiones acotadas; compila las funciones actuales literalmente y rechaza cambios del resto del código o de la semilla por hash. El bundle servido fue regenerado; no se maquilla su manifiesto sobre código viejo.
- UNVERIFIED: GitHub real, permisos de merge con las reglas actuales, deploy remoto y lectura del artículo público; navegador real, escritorio/estrecho/glance. Sin red, servicios ni credenciales reales.
- El audit-2.json citado por la plantilla no está montado; se implementó el brief específico. claudex/organismo no están disponibles; el vault se buscó directamente con rg. No se escribió estado vivo ni notas de personas.

## Contrato de pruebas

Inventario de cada aserción cambiada/retirada y razón: [ASSERTION-CHANGES.md](ASSERTION-CHANGES.md). El diff de git contra 44de0d2c0 incluye todos los cambios de actores, fixtures y aserciones. Sólo se retira el requisito de segunda persona; la aserción del correo pasa a false por el requisito explícito adicional del brief. No se debilita ninguna aserción de compuerta automática.

## Decisión

EN JUEGO: integridad de artículos y control de Javier → EVIDENCIA EXIGIDA: autor único conserva gates/revisión exacta y verificación del resultado público → EVIDENCIA QUE HAY: batería local offline y transporte git real local; sin efecto público → GO para integrar el código local; NO-GO para afirmar producción verificada.

ÉTICA: material §1/§2/§5 → Javier decide sobre su publicación; lectores pueden confiar en procedencia veraz; no se inventa revisión lingüística ni se envía correo.

## CANON

| Ruta leída | Aplicación concreta |
|---|---|
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/standard/CORE.md` | L1: retirar la compuerta humana inventada y conservar la protección automática. L5: separar publicación simulada de GitHub/deploy real y de inspección visual. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt` | No inferir autoridad para publicar en producción, modificar reglas, enviar correo o instalar dependencias del encargo de código. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/AGENTS.md` | Cargar sólo las disciplinas y fuentes solicitadas; no convertir ausencia del audit montado en hallazgos inventados. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/disciplines/SOFTWARE_ENGINEERING.md` | Tres regresiones observadas rojas antes de implementar; conservar SHA, diff confinado, privacidad, traducción y reconciliación; ejecutar aceptación completa. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/disciplines/VISUAL_ENGINEERING.md` | Seguir el flujo y textos definidos por el operador; probar el controlador y servir bundle coherente. Sin navegador real no afirmar validación visual. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/identity/README.md` | No rediseñar identidad; conservar activos y sistema existentes en el cambio de interacción solicitado. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt` | No cambió el diseño porque el encargo retira una aprobación; se conservan estilos, tipografía y composición existentes. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt` | No cambió nada de símbolos: no se crean marcas, iconos ni reinterpretaciones. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md` | Textos visibles Publicando y Publicado y verificado; los nombres internos de estados no se convierten en instrucciones para Javier. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/disciplines/WORTHY_WORK.md` | No trasladar trabajo rutinario al revisor humano como compuerta. La batería local no acredita la operación pública. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/disciplines/HIGH_CONSEQUENCE.md` | Mantener intent-before-effect, comprobación del candidato exacto y relectura de checks antes del merge; no anunciar producción probada. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/disciplines/COMMUNICATION.md` | El botón inicia la publicación y los mensajes describen su estado; no esperar aprobación inexistente. |
| `/srv/fcmo/agents/repos/FCMO-Agent-Hub/policy/FCMO_ETHICAL_MORAL_CONSTITUTION_V1.md` | Javier conserva control de su texto; los lectores no reciben una atribución falsa de revisión humana de inglés/chino. Correo apagado y ningún envío externo. |

Pendientes fuera de propiedad y continuación: sección `studio-un-autor` al final de [NEEDS.md](../NEEDS.md). No se declara cerrada la misión general de Claudex ni una campaña BONK.
