# L30 — candidato de integración seguro para escritores activos

## Resultado

Se integró `origin/main` `c01761726d2ea057f2aa3fb18377d3bdbe222005` (16 commits remotos posteriores a la base L29) en `c5/l29-main`, mediante `9a3ee2a99cb3c7b42a273733cff4e38ed0b0116b`. Una segunda lectura remota detectó `2f7bfb5c619486663b6c11b274f48a1b45c62e0b`, un commit nuevo del escritor de salud; se integró también, en `f9a9d1d8ce947f3e4defecba7fa7a97368091136`. El candidato incluye los 17 commits remotos observados. El fetch final después de la suite confirmó que main sigue en `2f7bfb5`, sin nuevos commits pendientes de integrar. Código adaptado en `bdc640a`. Autor de los commits de este carril: Codex <noreply@openai.com>.

Se eligió **(a): conservar el ledger en main**. El prompt local de la tarea 3 todavía exige agregar una línea a `ops/publication-desk/LEDGER.jsonl`, y seis commits recientes de `javo-27` confirman escrituras efectivas allí. No hay evidencia de que la tarea remota haya cambiado a `ops-ledger`. Una migración completa exigiría cambiar tarea, lectores y permisos remotos, fuera de esta entrega sin escrituras remotas. Mantener la ruta actual evita cortar al escritor o presentar ausencia como historial vacío.

La migración aislada queda diferida. `ops/publish_ledger.py` se conserva como herramienta de ensayo local; no se creó ni publicó ninguna rama de ledger. Se actualizaron `LOCALIZATION.md`, `ops/publication-desk/README.md` y `docs/PUBLISHING-SETUP.md` para describir el estado vigente y exigir que escritores y lectores se cambien juntos antes de una futura eliminación.

## Conservación y resolución causal

El único conflicto de Git fue modify/delete en `ops/publication-desk/LEDGER.jsonl`. Se conservó exactamente el blob del remoto, sin reserializar JSON, ordenar líneas ni combinar copias atrasadas:

- Remoto y candidato: **71 registros**, **327348 bytes**.
- SHA-256: `39e5bd7dfbb78290a3602253e32c7ee340b7104cb5b69ecf913a9ae8e329c8c5`.
- IDs únicos, orden cronológico UTC y timestamps con zona: válidos.
- Los 65 registros usados por L29 en `832ddcd` son un prefijo byte por byte del ledger actual; las seis activaciones posteriores permanecen intactas.
- Último registro: `publication-desk-20261007T004206Z`.

Se comprobaron **108 archivos idénticos al remoto**: todos los archivos de `corpus/`, `PRODUCTION_STATUS.md`, `site/data/newsroom-status.json` y `site/data/stories.v2.json`. Los datos generados restantes de la actualización remota se conservaron mediante el merge; no hubo conflictos en corpus ni estados.

Los gates detectaron un conflicto semántico que Git no señalaba: main había actualizado `release-src/` y los packs nativos, mientras el overlay congelado y el recibo seguían ligados al árbol anterior. El primer `verify_release.py` rechazó 4/7 compuertas: hashes de overlay, recibo y ensamblado/identidad. Se corrigió con `python3 tools/build_final_release.py` y `python3 tools/build_ready_receipt.py`. No se editaron hashes a mano ni se debilitó una compuerta. La primera regeneración conservó la revisión de Redata con seis claims y cinco limitaciones que ya estaba en main y sus idiomas.

La suite completa posterior detectó **12 fallos y 1 error**: el corpus había seguido avanzando después del último newsroom, dos registros incorporaban la etiqueta `NOT_ESTABLISHED`, faltaban rótulos UI para los nuevos códigos y el test de primera publicación suponía que el ledger upstream ya estaba actualizado para todo registro nuevo. Se corrigió la incompatibilidad en su causa:

- `tools/taxonomy.py` y los dos esquemas cerrados (`record.v3`, `stories.v2`) aceptan explícitamente `NOT_ESTABLISHED`, conservando esa etiqueta literal. No se convierte a DEMONSTRATED, CLAIMED ni otra evidencia más fuerte. El test nuevo demuestra conservación y rechazo de una etiqueta desconocida.
- Los catálogos EN/ES/ZH incluyen rótulos para las nuevas etiquetas cualificadas, `resolved` y `zh-CN`; la prueba de todos los enums permanece estricta.
- `release-src/` se reconstruyó desde el corpus remoto mediante ingest, sincronización JSON/JSONL, importación de los idiomas fuente, reconciliación y validación. Sin traducción generativa ni red pública. Los packs conservan los valores/provenance de PD1 y usan las nuevas deltas de ARB.
- Los desks locales se ejecutaron con `--offline`. Se conservaron **46 recibos de investigación idénticos**, después de comprobar su firma contra el brief actual; los cuatro nuevos declaran `cited_public_sources_reopened=0`, `reachable_sources=0` y `exhaustive_web_search_claim=false`. No se afirma re-investigación de sus fuentes. Se añadieron cuatro gráficos FCMO de explicación, que no son evidencia.
- Se regeneraron overlay y recibo otra vez. El overlay derivado contiene **50 registros** con todos sus idiomas. El **Story/status de producción conservado del remoto contiene 46 historias live**, 558 rutas; no se regeneró ni se adelantó artificialmente ese ACK. Su corpus más reciente todavía debe recorrer el newsroom y los controles de producción.
- El test del ledger de primera publicación conserva las comprobaciones de todas las entradas congeladas y verifica el fallback documentado para registros recién recibidos todavía sin entrada. El negativo de cuarentena masiva ahora corrompe más del 20% real del corpus creciente, conservando el umbral del código; diez registros ya no superaban ese límite al crecer la entrada.

`python3 tests/oraculos/verificar_generador_newsroom.py` pasa sin alterar su comparación estricta entre corpus actual y release derivado. El preflight real, sin mutación, elige `rebuild`, `CONTENT_AND_BUILDER_CHANGED`, `PUBLIC_DELTA_PENDING` para la release entrante `newswire-befd6e41ea51b790970a41c2`; no la confunde con el ACK publicado anterior. Esto verifica la decisión local de reconstrucción, no la ejecución del workflow ni su resultado vivo. **No se modificó ningún gate para ocultar el drift**. Los bytes de corpus, ledger y estados remotos siguen intactos.

## Escritores y lectores revisados

| Escritor / superficie | Destino real y evidencia | Decisión L30 |
| --- | --- | --- |
| Mesa de publicación, tarea programada 3 | Prompt `tareas/3-mesa-publicacion.txt`: escribe solamente los dos `part-desk.json` y el ledger en main; exige fetch/reconciliación antes de escribir. Commits `000a61c`, `0a61c8b`, `77df5c1`, `e7d72d7`, `6e76970`, `db70a7f`, por `javo-27`, modifican sólo el ledger. | Conservar ruta, historial y contrato de escritura. El prompt externo no se modificó. |
| Newswire Bridge, `newswire-bridge.yml` | `git add -A -- corpus`, rechazo de staging fuera de corpus, fetch y reintentos de push a main. | Corpus idéntico al remoto; no escribe el ledger. |
| Newsroom autónomo, `daily-refresh.yml` | Staging acotado a `release-src`, `release-overlay`, `site`, `READY_TO_PUBLISH.md`; rechaza cambios fuera de alcance y descarta/reconcilia builds si main cambia. | Se conservan sus salidas remotas y su protocolo de concurrencia; no escribe el ledger. |
| Estado de salud, `operator-alerts.yml` | `tools/status_report.py`; agrega únicamente `PRODUCTION_STATUS.md`, commit y rebase antes del push. | Estado idéntico al remoto; no escribe el ledger. |
| Pages, `pages.yml` | Despliegue y promoción de `refs/tags/lkg` tras live verify; no commit del ledger. | Sin ejecución ni activación remota en L30. |
| Correo, `dispatch-email.yml`, `dispatch-pieces.yml` | Dispatcher y persistencia de intents/estado de correo, independientes del historial de la mesa. | Sin cambio a sus contratos L29 ni envío real. |
| `ops/publish_ledger.py` | Sólo plan/creación en bare local explícito; árbol huérfano exclusivo del ledger y compare-and-swap. | Herramienta futura; no ejecutada aquí para migrar el ledger real. |
| `tools/migrate_pd1_desk.py` | Migración histórica de valores exactos a packs nativos; no agrega registros al ledger. | Sin ejecución ni cambio. |
| Tareas 1 y 2 | Prompts del motor ARB y la mesa de economía/política: trabajan en ARB, no en el ledger Newsletter. | Sin cambio. |

Se revisaron los 13 workflows y las referencias al ledger en `ops/`, `tools/`, pruebas y documentos. **Ningún workflow referencia `LEDGER.jsonl` ni ejecuta `publish_ledger.py`.** El escritor activo comprobado es la tarea 3, no un workflow dedicado. No se encontró otro append tool del ledger en el repositorio: la persistencia de la mesa está especificada en su prompt y confirmada por historia Git. No se inspeccionó la configuración privada actual de ChatGPT; la lista distingue contrato local y commits observados de configuración remota no consultada.

Los lectores externos L0/L7 están referenciados en el plan de campaña; su implementación/configuración activa no está en este árbol. Se conserva su ruta vigente y la prueba de historial real falla si el archivo falta. `reports/L1b-check.py` es un oracle histórico fijado a otras bases, no un escritor ni un gate de L30. Para migrar después: pausar/reconciliar escrituras, capturar el último blob, sembrar/verificar la rama aislada, cambiar tarea y todos los lectores, demostrar un run nuevo y sólo entonces retirar el archivo de main.

No se aplicaron rulesets. Las propuestas L11 y Studio de L29 siguen pendientes de decisión del operador: activar reglas que rechacen pushes directos podría cortar bridge, newsroom, estado y mesa aunque el merge sea correcto. L30 conserva los escritores existentes; no afirma que esas propuestas hayan sido activadas o verificadas remotamente.

## Validación

- Red-first: `5ccc51c` registra la prueba de conservación del ledger antes del merge. `python3 -m unittest tests.test_publication_ledger` falla entonces con un fallo por ledger no seguido. Tras conservar el blob remoto: **3 tests OK**, incluidos historial real, orden UTC e IDs únicos.
- `python3 -m unittest discover -s tests`: **814 tests, OK (4 skipped), 278.188 s, exit 0**, en la corrida final. La primera corrida roja fue de 813 tests, 12 fallos y 1 error, 274.293 s; el test de no establecer evidencia añade uno en la final.
- `python3 tools/verify_release.py`: **7/7 PASS**, exit 0, **50 registros y 0 traducciones pendientes** en el overlay ensamblado.
- Red adicional `cc1f670`: el nuevo test de `NOT_ESTABLISHED` falla por `CLAIM_LABEL_UNKNOWN` antes del adaptador. Después, suite focalizada Story/localización: **73 tests OK**.
- Oracle estricto del generador compuesto: **PASS**, sin cambio a sus controles.
- Conservación byte por byte del ledger y de los 108 archivos de corpus/status/Story: **PASS**.
- `git diff --check`: **PASS**; conflictos Git resueltos.

Evidencia local no publicada: `_audit/l30/unittest.txt` (corrida roja), `unittest-final.txt`, `release-initial.txt`, `release-final.txt`, `ledger-final.json`, `not-established-red.txt`, `adapter-locales-green.txt`, `generator-green.txt`. Estos logs son evidencia local de esta corrida; el arquitecto debe repetir los controles fuera de la caja. No se ejecutó aceptación de navegador en este carril ni se afirma estado del sitio vivo.

Para reproducir la conservación desde este candidato:

```sh
python3 -m unittest discover -s tests
python3 tools/verify_release.py
python3 - <<'PYCHECK'
import hashlib, subprocess
from pathlib import Path
from ops.publish_ledger import validate_ledger
ref = '2f7bfb5c619486663b6c11b274f48a1b45c62e0b'
path = 'ops/publication-desk/LEDGER.jsonl'
remote = subprocess.check_output(['git', 'show', f'{ref}:{path}'])
local = Path(path).read_bytes()
assert local == remote
assert len(validate_ledger(local)) == len(validate_ledger(remote)) == 71
print(len(local), hashlib.sha256(local).hexdigest())
PYCHECK
```

## Continuación y push del arquitecto

Primero repetir suite, 7 gates y `python3 ops/publish.py --check` con el navegador real. Revalidar `origin/main` inmediatamente antes de promover: si avanzó, integrar sus nuevas líneas/corpus/estado y repetir aceptación. Los 71 registros corresponden al SHA capturado, no son un contador fijo para corridas futuras. Nunca usar force-push ni restaurar el ledger a este snapshot después de nuevas escrituras.

**Orden exacta para promover a main, sólo si el arquitecto y D1 autorizan ese destino y las protecciones vigentes lo permiten:**

```sh
set -eu
git fetch origin
git merge-base --is-ancestor origin/main c5/l29-main
# Si la comprobación anterior falla, detenerse e integrar el nuevo main.
git push origin c5/l29-main:refs/heads/main
```

El push es fast-forward: si un escritor avanza main en la carrera, Git debe rechazarlo y hay que reconciliar, nunca forzar. Ejecutar las líneas de forma condicionada al éxito de las comprobaciones y la aceptación externa. Si se requiere PR, la orden exacta para subir sólo el candidato es `git push origin c5/l29-main:refs/heads/c5/l29-main`; aprobación y merge quedan al arquitecto/operador. Estos comandos están documentados, **no ejecutados**.

No se hizo push, dispatch de workflow, despliegue Pages, modificación de permisos/secretos ni otra escritura remota. No se cambiaron otras worktrees ni la rama local main. La única red utilizada fue fetch autorizado de origin.

**Resumen:** candidato local con L29 y los 17 commits observados de main, 71 registros intactos y adaptador compatible con la evidencia nueva sin subir su fuerza. Migración aislada diferida. Suite final 814 tests OK y release 7/7. Navegador, decisión de push y prueba de producción pertenecen al arquitecto.
