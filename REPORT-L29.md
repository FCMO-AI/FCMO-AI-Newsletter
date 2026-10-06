Matías: campaña 5 integrada localmente en `c5/int-1005`, desde `origin/main` 508a60b.
Studio/translate se fusionó primero; email-kit después, conservando ambos propósitos.
Una pieza aprobada en Studio conserva la intención de correo y llega al dispatcher común.
Studio lee el estado confirmado de L28b y muestra «Correo programado ✓» en los tres idiomas.
L27e corregido con prueba roja previa: usa el ID del POST 201/200 sin volver a listar tags.
Las ramas antiguas se auditaron; sólo publicación aportaba trabajo único todavía necesario.
Validación final: 813 tests OK (4 omitidos); gates 14/14 para tres proveedores; release 7/7.
Sin push remoto, correo real ni Kit live; la aceptación visual sigue pendiente por falta del ejecutable Chromium.

# L29 — integración y límites verificados

Entrega local del 2026-10-06. No se modificaron `main`, `origin/main` ni otras
worktrees mediante esta tarea. El resultado está preparado en la rama solicitada;
no se afirma despliegue, entrega de email ni operación autónoma en producción.

## Integración y resolución

- `d3baf04`: merge de `c5/studio-translate`, que incluye Studio live. En
  `READY_TO_PUBLISH.md` se conservaron el corpus y las identidades más recientes
  de main, evitando volver a 43 historias activas.
- `832ddcd`: merge de `c5/email-kit`, con L26–L28b. `REPORT.md` conserva ambos
  informes; Pages conserva piezas editoriales, rollback, formularios y privacidad.
- `6ce627e`: merge del trabajo único de `c5/pub`. Se añadieron publish-gate,
  validación completa en Pages, restricciones de deploy/rollback manual desde
  main, solicitud de ruleset sin efectos remotos, ensayo de snapshot inmutable y
  migración aislada del ledger. Se conservaron CODEOWNERS de Javier/Matías y el
  checker actual `ops/publish.py --check`; el ensayo incluye piezas e higiene.
- `405c90c`: unión Studio/correo, dependencias de CI y recibo regenerado. La
  suite incorporada necesita age y PyYAML: los workflows ahora los instalan.
  No se ejecutaron esas instalaciones ni los workflows remotos en esta sesión.

Al unir L11 con Studio se detectaron dos productores del check requerido
`publish-gate`. `006f5f1` conserva la prueba roja (un fallo): dos workflows
compartían ese nombre. La corrección `9febd8f` da a `release-validate.yml` el nombre
visible `release-integrity`, conservando sus controles; sólo `publish-gate.yml`
produce el requisito. Los tres workflows de publicación instalan age, PyYAML y
las dependencias de navegador/axe necesarias para la suite integrada.

La integración agregó una superficie pública de privacidad y cambió el árbol
medido. El primer control de release rechazó el recibo viejo: 2064 frente a 2065
archivos y digest distinto. Se regeneró con `tools/build_ready_receipt.py`, sin
editar hashes a mano ni rebajar gates. Mantiene 558 rutas, 138 rutas Story y
46 historias activas; la identidad del corpus y el overlay permanecen actuales.

## Unión de Studio con el dispatcher

El archivo aprobado `piece.json` contiene `distribution.email=true`; la
aprobación independiente registra revisión humana en `provenance.json`.
Workspace transporta esos archivos al candidato público y PaperBuilder los
copia a la publicación. La colección L28b exige bytes idénticos al LKG,
páginas revisadas e identidad de despliegue estable. Después reserva claves
permanentes antes de programar y vuelve a comprobar el contenido publicado.

`tools/email_dispatch.py --pieces` es el punto de entrada común para
`--collect`, `--claim` y `--send`. El workflow de piezas usa ese punto de entrada;
los proveedores y las protecciones de L27/L28b conservan su funcionamiento.

Se resolvió la incompatibilidad de los reports L28a/L28b: Studio ya no espera
`ops/email-dispatch/pieces/<id>.json` en main. Consulta por GET la proyección
`email-dispatch-state:dispatch.json`, únicamente después de su comprobación de
publicación web. Exige reservas de producción, esquema válido y QUEUED con ID y
fecha en EN/ES/ZH. Registros parciales, de prueba, inválidos, ausentes o inciertos
no activan el indicador. No requiere refrescar main ni redesplegar. Las claves
por pieza/idioma son de por vida; una enmienda no provoca reenvío.

La interfaz dice «Correo programado ✓» / «Email scheduled ✓»: QUEUED demuestra
programación confirmada, no entrega. Los documentos del hook se actualizaron y
el bundle se reconstruyó sin descargar paquetes, con manifest ligado a fuentes.

`tests/test_studio_email_seam.py` usa Store, traducción fake, revisión de Matías,
Workspace con git local, build real, colección contra los bytes construidos,
StateStore con Contents sintético, el CLI común y lectura HTTP local del estado
por Studio. Prueba reservas antes del despacho, tres programaciones ficticias y
cero nuevas en la repetición; además ausencia de estado y negativos de lectura.
La verificación de Pages y el proveedor son fronteras simuladas, no producción.

Prueba roja `59b168a`: dos errores, CLI sin `--pieces` y hook incompatible.
Prueba verde posterior: seam más publicación protegida, 13 tests OK.
El test viejo del recibo L28a fue sustituido por el contrato real integrado.

## L27e

Prueba roja `72ed8a6`: 28 tests, seis fallos y dos errores; ambos POST 201/200
fallaban ante un listado atrasado y los negativos demostraban la segunda lista.
Fix `d6b2673`: `ensure_tags` usa `response.tag.id` entero positivo para un tag
creado/resuelto por POST, sin re-listar ni repetir una mutación incierta. IDs
explícitos siguen funcionando; se conserva la comprobación de nombres duplicados
y tags distintos por idioma. Respuesta perdida o inválida bloquea.

Prueba verde: 28/28. La fixture HTTP devuelve 201 al crear y 200 al resolver un
nombre existente, mientras oculta ambos del listado; no hubo llamada a Kit real.

## Ramas antiguas: git cherry y decisión

Se ejecutó `git cherry HEAD c5/<rama>` después de los dos merges solicitados y
otra vez sobre el resultado integrado. `+` significa patch-id diferente, no
necesariamente funcionalidad ausente; se contrastó código, historia y pruebas.

| Rama | Resultado inicial | Decisión y razón |
| --- | --- | --- |
| studio-int | Sin salida | Ya contenido por ascendencia en Studio/translate. |
| studio-a1 | Sin salida | Build editorial y renderer ya contenidos en Studio. |
| studio-a2 | Sin salida | Storage/auth y publicación duradera ya contenidos en Studio. |
| studio-b | Sin salida | Editor/interfaz y estilos ya contenidos en Studio. |
| agents | `+ 9d9986e` | Cubierto por `2d8257a` de main y evolución posterior; no reintroducir artefactos viejos. |
| fresh | `- 4fe45c4`, `- d3e2b5f`, `+ a34df04` | Tests equivalentes; implementación cubierta por `af91efc` de main y endurecimientos posteriores. |
| pub | Cinco `+` | Controles protegidos y migración ausentes: integrados, conservando los contratos actuales. |
| email | Sin salida | L26 ya incluido por ascendencia en email-kit. |

En el `git cherry` final, pub también queda sin salida. Agents y fresh conservan
sus signos iniciales: deliberadamente no se fusionaron commits ya cubiertos con
artefactos/recibos obsoletos. Higiene, citas versionadas, feeds y frescura
independiente se verifican en el código y en los gates actuales.

Parches individuales, sin repetir los compartidos entre ramas Studio:

- `e08b037`: Presente; registro histórico de la especificación A1, sin trabajo nuevo.
- `f0223ab`: Presente; registro histórico de la especificación A2, sin trabajo nuevo.
- `132d8d5`: Presente; marco y CSS del ensayo ya integrados.
- `e525dc5`: Presente; regresiones de durabilidad y documento cerrado ya integradas.
- `9091186`: Presente; interfaz de editor, idiomas y publicación ya integrada.
- `e854f16`: Presente; contrato de build editorial ya integrado.
- `419255b`: Presente; storage privado, autenticación y publicación reconciliada ya integrados.
- `5b78665`: Presente; errores localizados e invalidación de preview ya integrados.
- `3d9d68e`: Presente; rechazo de edición con traducción ausente ya integrado.
- `1ddaf23`: Presente; readiness y congelación atómica de revisión ya integradas.
- `b0167ae`: Presente; evidencia histórica A2 conservada.
- `d05095b`: Presente; pipeline editorial humano validado ya integrado.
- `6a93224`: Presente; evidencia histórica A1 conservada.
- `84ff852`: Presente; regresiones API/preview de integración ya integradas.
- `f933e90`: Presente; rechazo de bundle viejo y publicación HTTP con gates ya integrados.
- `d3f7a7a`: Presente; API y preview de producción ya integrados.
- `eae30e1`: Presente y actualizado; bundle reconstruido para el hook de correo.
- `c0987ce`: Presente; correcciones de notas, preview, carga e idiomas ya integradas.
- `15a9732`: Presente; checks agrupados, móvil, inglés y renderer ya integrados.
- `9d9986e`: Cubierto/superado; main 2d8257a contiene citas/frescura, y conserva evolución posterior.
- `4fe45c4`: Patch equivalente presente; regresión de heartbeat congelado ya cubierta.
- `d3e2b5f`: Patch equivalente presente; fixture completa ya cubierta.
- `a34df04`: Cubierto/superado; main af91efc aporta frescura independiente y hoy excluye historias no live.
- `7138874`: Único querido e integrado; pruebas de publicación protegida y ledger aislado faltaban.
- `c2e1f65`: Único querido e integrado con adaptación; faltaban workflow, gates y herramientas de migración.
- `b8eca86`: Integrado con adaptación; recibo se regenera actualmente y checks excluyen credenciales Ghost.
- `4dac3a5`: Único querido e integrado; migración conserva orden UTC e IDs únicos.
- `dcbb37c`: Único querido e integrado; evidencia histórica y límites de activación útiles para continuar.
- `6a90a16`: Presente; L26 ya está en email-kit, sin trabajo único pendiente.

## Ledger y activación remota

El archivo retirado se recupera de `832ddcd:ops/publication-desk/LEDGER.jsonl`:
65 registros ordenados; SHA-256
`4437c732b459fa0678330fde26fce441a431d66cbdc92be6ceb3b490d6b30f2a`.
Se probó la migración en un bare aislado `_audit/l29/ledger.git`: árbol huérfano
exclusivo del ledger, bytes idénticos y segunda ejecución idempotente. No se creó
una rama ops-ledger en el repositorio de producto ni en el remoto. Antes de
integrar en el main remoto, revalidar el último ledger allí, migrarlo y adaptar
los lectores/escritores operativos según PUBLISHING-SETUP; no reactivar una
mesa que interprete su ausencia como historia vacía. LOCALIZATION ya identifica
la rama separada como destino y expresa ese prerrequisito.

Las propuestas de protección L11 y Studio L25 no son una activación remota:
L11 propone cero bypass; Studio permite exclusivamente la integración Actions
para preservar escritores autónomos. No se aplicó ninguna de las dos durante
L29. El operador debe resolver y verificar esa frontera con los writers reales
antes de activar una propuesta que bloquee bridge/newsroom. Tampoco se
modificaron secretos, permisos remotos, audiencia ni configuración de Kit.

## Validación y continuación

La instalación local existente de Playwright 1.63 no se resuelve por defecto.
Se localizó y se pasó explícitamente al oráculo: Chromium no arrancó porque
falta su ejecutable, confirmado por `BROWSER_UNAVAILABLE`. No se descargaron
paquetes ni navegador y no se afirma aprobación visual.

El dogfood estricto con `--browser` terminó incompleto, 6/25. Su copia de entrada
se creó mientras se regeneraba el recibo y conservó el recibo anterior. La
repetición aislada de `build_ready_receipt.py --check` sobre esa copia reproduce
el rechazo por 2064/2065 archivos y digest; ese no es el recibo actual de esta
rama. El checker sobre la worktree corregida pasó suite, release, higiene y
14 gates, y se detuvo en el navegador. No se afirma un recorrido dogfood
completo ni se cambió su checker por uno de fixture para obtener verde.

| Control | Resultado observado |
| --- | --- |
| `python3 -m unittest discover -s tests`, árbol final `9febd8f` | **813 tests, OK, 4 skipped**, 664.632 s, exit 0. |
| Primera suite completa | 812 tests, OK, 4 skipped, 889.367 s. |
| Suite email | **100/100**, 42.103 s. |
| Seam HTTP y publicación protegida | 13/13, 11.515 s. |
| Publicación protegida, ledger y Studio live tras corregir el nombre | **27/27**, 364.856 s. |
| Web | **9/9**; bundle y manifest coherentes con fuentes/lockfile. |
| Kit, Brevo y Listmonk | **14/14 gates por candidato**; higiene PASS; 558 rutas cada uno. |
| `python3 tools/verify_release.py` | **7/7**, con recibo regenerado. |
| `python3 ops/publish.py --check --out _audit/l29/publish-check` | Suite 812 OK, release 7/7, higiene y gates 14/14; **exit 2 en navegador**. |
| Oráculo con módulo Playwright existente configurado | **BROWSER_UNAVAILABLE**, Chromium no existe; exit 1 del oráculo. |
| Dogfood estricto con navegador | **Incompleto, 6/25**, exit 1; copia con recibo previo, no aceptación final. |
| CLI común con master off y bundle ausente | `SKIP pieces disabled`, exit 0, sin leer bundle ni crear proveedor. |

Las cuatro omisiones corresponden a dos pruebas de navegador, una de axe-core
y el negativo del renderer ausente, ya integrado. Los mensajes de gate negativo
y de solicitud/rollback de protecciones dentro de las suites corresponden a
fixtures y comandos mock; no hubo solicitudes remotas ni cambios de protección.

**La aceptación de software y gates locales está verde. La aceptación visual y
el recorrido dogfood completo permanecen abiertos.** No se presenta el exit 2
del checker como un PASS ni se atribuye entrega real a los providers ficticios.

Evidencia local privada en `_audit/l29/` (no forma parte de la publicación):
`l27e-red.txt`, `l27e-green.txt`, `seam-red.txt`, `seam-http-green.txt`,
`email-tests.txt`, `full-tests-initial.txt`, `full-tests-final.txt`, `publish-check.txt`,
`release-final.txt`, `gates-kit.txt`, `gates-brevo.txt`, `gates-listmonk.txt`,
`web-tests.txt`, `browser.txt`, `browser-installed-module.txt`, `protected-final.txt`, `check-name-red.txt`,
`git-cherry.txt`, `git-cherry-final.txt`, `dogfood/summary.json`,
`dogfood-receipt-check.txt` y `ledger-migration.json`.

Reproducción sin proveedor ni credenciales reales:

```sh
python3 -m unittest discover -s tests
python3 -m unittest tests.test_studio_email_seam
python3 -m unittest discover -s tests -p 'test_email*py'
npm --prefix studio/web test
python3 tools/verify_release.py
python3 ops/publish.py --check
```

Para los tres candidatos se usaron los comandos de L27/L28b, con configuración
pública sintética, `--editorial editorial`, build, copia del glosario,
`tools/gates/run_all.py` y `tools/validate_agent_hygiene.py`. Se verificó
sintaxis Python, YAML y `git diff --check`. No se debilitó ningún gate ni se
usó `--fixture-build` para declarar aceptación de publicación.

En un entorno con Playwright/Chromium/axe-core ya instalados, configurar
`PLAYWRIGHT_MODULE`, `CHROME_PATH`, `NODE_PATH` y `AXE_CORE_PATH`, repetir
`ops/publish.py --check` y `sh studio/dogfood/run.sh --browser --keep _audit/l29-browser`.
Inspeccionar los resultados a 390/1440 y en los idiomas requeridos. Cualquier
seed/MIME/delivery, producción Pages, migración remota y continuidad automática
requiere una tarea autorizada posterior: está fuera de esta entrega sin efectos
externos. Conservar claves e intents permanentes durante cualquier rollback.

**Resumen:** Studio y email están conectados y L27e corregido con evidencia roja
previa. Se conservó el trabajo único de publicación, se evitaron regresiones del
corpus y se documentó cada rama antigua. Integración local verificada hasta la
frontera disponible; navegador y producción siguen sin demostración aquí.

Código integrado verificado: `9febd8f`; el commit de entrega sólo añade este informe y su enlace desde `REPORT.md`.
