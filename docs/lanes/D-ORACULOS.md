# D: integración de Cartas y migración de tres oráculos

Carril `nl-d-integra`, 2026-10-26. Contrato: `design/d-libro/CONTRATO.md` y
solicitudes de integración de `NEEDS.md`. Sólo se migran las tres familias
expresamente autorizadas; las pruebas de ensayos, privacidad, localización,
release y presupuestos de página permanecen intactas.

## 1. Portada: frescura y plan

**Antes:** `test_v4_front_freshness` / `test_v4_front_plan` buscaban cuatro
`article.plate-card` sobre Bone después del héroe. El nuevo árbol D no los tiene;
se observaron errores de selector en EN/ES/ZH en la ejecución previa.

**Después:** `.d-rank` y sus cinco `li[data-story-id]` deben coincidir exactamente
con `front_order[:5]`. El héroe y la fila 01 representan el mismo registro, como
exige R4. Se resuelven los cinco destinos y se comprueban idioma y titulares;
las treinta filas siguientes conservan orden, identidad, titular y destino.
La unicidad se exige sobre tabla + wire, sin contar dos veces la representación
del héroe. Las ventanas de 48 horas, preferencia por elegibilidad, todos los
casos unitarios de ordenación, archivos de edición y las 14 compuertas se
conservan. La ventana del héroe sigue teniendo la excepción editorial previa;
las cuatro filas restantes mantienen ventanas no decrecientes.

## 2. Primera pantalla móvil

**Antes:** `test_v4_mobile_first_viewport` exigía la navegación C6 con Correcciones
arriba y cinco tabs inferiores. Se observaron los tres fallos de destinos.

**Después:** un encabezado, seis destinos D (Hoy, Cartas, Temas, Archivo, Método,
Buscar), tres idiomas con destinos exactos y Correcciones/Suscripción en el pie.
El HTML y los archivos locales se comprueban en los tres idiomas. El oráculo real
abre y cierra el menú nativo con Enter: exige control y enlaces de 44 × 44 px,
visibilidad completa del menú, restauración del titular y ausencia de tabs.
El límite del encabezado corresponde a los 68 px D más la regla de 1 px.
Se mantienen titular con comienzo ≤460 px y final ≤844 px, señales de frescura
enteras sobre él, anchura, consola, recursos, cobertura y navegación de escritorio.
Las antiguas pruebas de solapamiento de tabs se trasladan a apertura/restauración
del menú, con mutaciones negativas de medidas, destinos, estado y encabezados.
Los demás casos sobre copy de transporte, CSS generado y texto largo siguen.
La ejecución con mediciones simuladas comprueba el juez, no acredita Chromium.

## 3. Tipografía

**Antes:** `test_paper_build` exigía tres precargas. Se observó `2 != 3`.

**Después:** exactamente dos precargas, con los nombres completos de Inter Tight
y JetBrains Mono, ambas Latin WOFF2 locales existentes; ninguna Source Serif.
Se conserva el archivo Serif heredado para las superficies que aún lo usan,
la ausencia de TTF y las comprobaciones previas de subconjuntos. El presupuesto
HTML/JS/búsqueda permanece intacto. El límite CSS de 114688 bytes no se aumenta.

## Integración y evidencia de regresión

Se elige `/letters/` para el índice D en EN/ES/ZH; `/cartas/` conserva su
redirección heredada y las piezas conservan sus rutas. Portada e índice consumen
la misma proyección de piezas publicadas y ediciones listas, con URLs e
imágenes bajo el prefijo real del build. La portada presenta hasta doce; el índice
conserva todos y las ediciones publicadas siguen enlazadas. Sin noticias, las
cartas publicadas todavía aparecen. Sin cartas, no se inventan tarjetas.
El CSS `d-letters.css` ya estaba incluido en el shell y no requería otra carga.
El índice EN incorpora además la proyección pública de Ghost. La portada mantiene
la exclusión de Ghost exigida por la prueba vigente; Ghost no aporta ediciones
nativas ni se presenta como traducción ES/ZH. Esas
ediciones usan documentos editoriales listos y muestran vacío cuando faltan.
No hay llamadas de traducción ni red; Ghost se sustituye por datos sintéticos.

La nueva batería `tests.test_d_letters_integration` falló antes de integrar por
falta del shelf D y del índice; después comprueba portada, índice, rutas,
metadatos, orden, recursos, ediciones pendientes y corpus de noticias vacío.
Los briefs se sanean mediante el alias externo `FCMO-Agent-Hub/`, sin modificar
`NO_MACHINE_PATHS`. La prueba previa también reprodujo el rechazo de esa compuerta.

Logs locales bajo el TMPDIR indicado: `before.log` (86 pruebas: cuatro fallos,
cuatro errores y dos omisiones; ejecución de diagnóstico, no suite completa),
`letters-before.log`, `targeted-final.log` y `acceptance-cartas.log`.
El primero cargó los oráculos previos antes de sus cambios: el texto de algunas
líneas del traceback procede del archivo ya editado; los valores de la aserción
registran la ejecución original. No se presenta como una suite de base inmutable.

## CANON

Rutas relativas al checkout canónico externo `FCMO-Agent-Hub/`, HEAD leído
`9f726f25276d7b9da910eec6bdb2784aec3f4361`, igual a la revisión requerida.

- `standard/CORE.md`: la suite local acredita integración; no autoriza despliegue ni demuestra producción.
- `runtime/FCMO_RUNTIME_V1.txt`: la rama heredada se continúa; no se reinicia ni se atribuye trabajo anterior al carril.
- `AGENTS.md`: se cargó el ruteo vigente y se buscó antecedente en la única vault; CLI KB ausente, búsqueda directa de la galería.
- `disciplines/SOFTWARE_ENGINEERING.md`: se reprodujeron los rojos antes de conectar los registros y migrar los selectores.
- `disciplines/VISUAL_ENGINEERING.md`: el oráculo mide menú y destinos; no se confunde el juez sintético con una inspección visual.
- `identity/README.md`: se sigue D aprobado y el shell FCMO AI existente; no se crea otra identidad.
- `identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt`: las precargas se limitan a Inter Tight y JetBrains Mono; no se agrega Serif para satisfacer C6.
- `identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt`: no cambió nada porque esta integración no modifica símbolos ni acentos.
- `identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md`: no cambió la atmósfera porque el contrato D aprobado ya la fija; no se rediseñan las superficies.
- `disciplines/WORTHY_WORK.md`: no cambió el objetivo porque se trata de integración local sin publicación ni promesa comercial; la suite no se llama prueba de producción.
- `disciplines/MEMORY_CONTINUITY.md`: se conserva NEEDS histórico y se documenta aquí la migración con su límite de evidencia.
- `identity/FCMO_EDITORIAL_SOCIAL_OS_v0.1.md`: no cambió copy porque se reutilizan documentos publicados; no se inventan nombres, cargos o cartas de la referencia.
- `disciplines/COMMUNICATION.md`: el reporte separa resultado local, omisiones y bloqueo CSS sin declarar 1:1.
- `governance/KNOWLEDGE_FRESHNESS.md`: el HEAD del Hub se verificó localmente; los resultados anteriores no se reciclan como aceptación del candidato actual.
- `commons/USO_CANON.md`: no se añade ceremonia comercial a una integración local reversible, sin enviar ni publicar contenido.

## Contrato Ghost conservado

La primera suite serial se interrumpió con salida 130 después de registrar rojos;
no se cuenta como aceptación completa. La reproducción aislada
`python3 -m unittest tests.test_community_rail` terminó `Ran 16 tests`,
`FAILED (failures=3)` (`ghost-before.log`). Dos casos rechazaban el nuevo campo
`authors` fuera de la proyección permitida; otro prohibía contenido Ghost en
cualquier portada. Se restituye la proyección exacta de cinco campos, sin
solicitar autores al proveedor. Portada usa las piezas locales; el índice EN
puede añadir Ghost, sin atribuir autor cuando no consta. No se modificó ninguna
aserción de `test_community_rail`; las nuevas regresiones de integración
comprueban también esa separación.

## Dependencia de Studio causada por Cartas

La suite serial completa sobre `dfb379754` terminó `Ran 1306 tests in
1861.442s`, `FAILED (errors=2, skipped=9)`, sin fallos de aserción. Ambos
errores eran de `test_studio_host`: preflight y probe rechazaban el bundle
versionado. La única fuente cuya huella difería del manifiesto era
`site-src/assets/css/essay.css`, modificada por Cartas en `4f01c7191`.

Se reconstruyó Studio en una copia temporal con el compilador offline existente,
sin red ni dependencias nuevas. Sólo se traslada su CSS expandido y se actualizan
la huella de esa fuente y la del artefacto CSS. El JavaScript original se conserva:
ninguna fuente JS cambió y el fallback completo sustituiría el editor por el
acceso offline. La diferencia de líneas CSS corresponde a la salida sin minificar.
`studio.server.bundle.ready()` confirma las huellas de todas las fuentes y
artefactos; las reglas D de Cartas están presentes en el CSS servido.

Las cuatro pruebas existentes de `tests.test_studio_host` pasan después de la
corrección (`studio-host-after.log`); se habían observado los dos errores antes
en la suite completa. Sus pruebas y las compuertas no se modificaron.
La aceptación serial completa se repite sobre el candidato corregido; el resultado
anterior no se presenta como verde.

## Aceptación final

Código congelado en `4adf19ae5`, con una sola suite a la vez y todos los comandos
con el TMPDIR solicitado. El último commit añade únicamente este recibo.

| Comando | Resultado observado |
| --- | --- |
| `python3 -m unittest discover -s tests` | `Ran 1306 tests in 1917.549s`; `OK (skipped=9)`, salida 0. Log `full-suite-final.log`. Ningún fallo o error; mismas nueve omisiones que la base declarada de 1270. |
| `python3 -m unittest tests.test_d_cartas tests.test_essay_template tests.test_essay_build` | `Ran 24 tests in 2.848s`; `OK`, sin omisiones. Log `acceptance-cartas-final.log`. |
| `python3 -m unittest tests.test_studio_host` | `Ran 4 tests in 1.566s`; `OK`. Preflight y probe reales en loopback pasan sin cambiar sus pruebas. |
| `git diff --check` y `git diff f90e376cb --check` | Limpios. |
| `python3 design/build_css.py --check` | Salida 1: `CSS FAIL: paper.css exceeds 114688 bytes`. `paper.css` tiene 115466 bytes, idéntico al de `origin/main` local `591aff151052f200d4dde063ae308edeaa32c530`. No se cambió el archivo ni su límite. |
| `python3 tests/oraculos/verificar_mobile_first_viewport.py` | Salida 1: `BROWSER_UNAVAILABLE`, módulo Playwright no disponible. No se instalaron dependencias. El programa de medición pasa `node --check`; las mutaciones del juez pasan, sin acreditar DOM físico. |

No verificado: navegador, capturas/comparación visual 1:1 y producción. No hubo
despliegue, red, llamadas de modelo ni cambios de configuración o servicios.
`NEEDS.md` histórico permanece intacto; la integración y los rojos de unittest D/Cartas
descritos allí se cierran mediante los cambios y pruebas de este documento.
