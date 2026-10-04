# Instalación de la publicación protegida

Estado de este cambio: propuesta y herramientas locales. Ningún ruleset remoto, token, tarea programada ni rama remota se modifica aquí.

## Protección de main

`ops/publish-ruleset.json` propone reglas activas para `refs/heads/main`: PR obligatorio, una aprobación de CODEOWNERS independiente del último push, revisión obsoleta descartada, conversaciones resueltas, sin eliminación ni force-push, y **publish-gate** actualizado respecto de main. El check se restringe a GitHub Actions (App ID 15368). No hay actores con bypass.

`.github/workflows/publish-gate.yml` corre en todos los PR a main, sin filtro de rutas, con permisos de lectura y sin secretos. Comprueba la suite y el mismo candidato mediante `ops/publish.py --check`. No ejecuta `pull_request_target`. Pages conserva sus gates propios, independientes del resultado de un check previo.

`.github/CODEOWNERS` usa `@javo-27`, cuenta evidenciada por el historial de la mesa. Antes de activar, comprobar que sigue teniendo acceso de escritura y añadir la cuenta real de Matías o un equipo con ambos como propietarios. Sin un segundo propietario, Javier no puede aprobar sus propios PR. Un nombre en el archivo no demuestra que GitHub lo haya reconocido.

Para revisar la solicitud sin aplicarla:

```sh
python3 ops/publish_ruleset.py
```

El script únicamente imprime JSON y la orden del administrador; no contiene un modo de aplicación ni llama a la red. Sólo después de integrar, de comprobar el check en un PR real y de resolver la automatización descrita abajo, el administrador puede ejecutar la orden mostrada. Debe conservar el ID del ruleset y consultar su estado efectivo. No basta con que la API acepte el JSON: un push directo de la identidad de la mesa debe ser rechazado, y un PR sin aprobación/check debe quedar bloqueado. No se hizo esa prueba remota en este carril.

**Prerequisito de continuidad:** `newswire-bridge.yml` y `daily-refresh.yml` todavía hacen `git push origin HEAD:main`. Estas reglas los bloquearán. Antes de activarlas hay que llevar esos cambios mediante PR con el check y una aprobación autorizada, o acordar otra arquitectura compatible. Con la revisión humana obligatoria para todo main, esos commits no pueden ser totalmente autónomos. No se añade un bypass al bot ni se debilita la revisión para ocultar esta incompatibilidad. El administrador debe resolverla antes de activar; Pages puede seguir publicando el main ya revisado.

El botón de Pages sólo acepta deploy/rollback manual desde main. La configuración del entorno `github-pages` también debe limitar el despliegue a main para que otros workflows/runs no obtengan permiso de despliegue. Restringir permisos de edición de reglas y workflows; los administradores con facultad de modificar reglas siguen siendo autoridades reales.

## Separar el ledger de la mesa

Este cambio deja de seguir `ops/publication-desk/LEDGER.jsonl` en la rama de producto. El histórico permanece en git. **Antes de integrar la eliminación**, guardar el SHA más reciente de main que todavía contenga el ledger; no usar una copia atrasada si la mesa agregó registros. Pausar sus escrituras durante la migración.

En un clon bare local independiente, preparar primero la migración sin escribir:

```sh
python3 ops/publish_ledger.py --source-ref SHA_CON_LEDGER --local-bare ensayo.git
```

Después de revisar el número de registros y hash, crear sólo la rama local `ops-ledger`:

```sh
python3 ops/publish_ledger.py --source-ref SHA_CON_LEDGER --local-bare ensayo.git --apply-local
```

El árbol huérfano contiene exclusivamente el ledger, con bytes intactos. Nunca modifica main ni hace push. Repetir la misma migración es idempotente; si existe una rama diferente, se detiene para no perder registros. La creación usa compare-and-swap y rechaza una creación concurrente. El administrador verifica los bytes, sube **únicamente** `refs/heads/ops-ledger:refs/heads/ops-ledger` desde ese clon, comprueba el hash remoto, y luego integra la eliminación del archivo de main.

Cambiar el prompt de la mesa (E4) por este contrato:

> Lee main para QA y traducciones, pero no hagas push a main. Propón los cambios de contenido mediante PR. Persiste exclusivamente el ledger público en ops-ledger, con checkout separado; conserva registros previos y run_id únicos. Si otra corrida avanza ops-ledger, vuelve a leer y une por run_id; conflictos con el mismo run_id se detienen. No copies código ni contenido del sitio a ops-ledger. No uses force-push. La rama de producto no contiene el ledger.

Rotar la credencial de la mesa a una identidad separada con **Contents: read/write**, limitada a este repositorio, sin permisos de Administration, Workflows, Actions, Pull requests ni bypass. El token no tiene un alcance por rama: la pérdida efectiva de push a main la impone el ruleset. Mover el archivo por sí solo no revoca permisos. El token de Javier para revisión/publicación no debe compartirse con la mesa. Si la mesa necesita crear PR, hacerlo mediante una identidad y canal separados cuya autorización no permita aprobar o integrar su propia propuesta.

Los lectores operativos del ledger (sonda L0 y fallback L7, fuera de este carril) deben pasar a leer `ops-ledger:ops/publication-desk/LEDGER.jsonl`. No se les debe entregar un ledger vacío cuando el archivo desaparezca de main. Verificar una corrida de la mesa con un nuevo run_id y main intacto antes de reanudarla.

## Ensayo sin red ni publicación

Requisitos: Python, git, Node, Playwright 1.63.0 y Chromium ya instalados. Si la instalación de Node no resuelve Playwright, configurar `PLAYWRIGHT_MODULE` a su ruta local. La falta de navegador bloquea el ensayo; no hay opción para saltarlo.

```sh
git clone --bare --no-hardlinks . ensayo.git
python3 ops/publish.py --dry-run --local-bare ensayo.git --ref HEAD --receipt ensayo-receipt.json
```

El script resuelve el commit una sola vez, clona esos bytes a un temporal y ejecuta las seis comprobaciones históricas, construye el periódico, ejecuta todos los gates, genera tarjetas OG, reconstruye el candidato final, repite los gates, comprueba el navegador y vincula la identidad. No mueve referencias del clon bare ni hace push. Los pasos locales descartan las variables de Ghost para no consultar contenido remoto ni usar esa credencial. Un recibo PASS identifica ese commit, y explícitamente dice que no hubo despliegue. Evitar reutilizar un recibo antiguo tras un fallo.

Para repetir el control negativo y el aislamiento del ledger:

```sh
python3 -m unittest tests.test_protected_publishing -v
```

La prueba negativa inyecta un script remoto en una edición y exige que el gate la rechace antes de llegar al navegador. El control de conservación compara todas las referencias del bare antes/después, incluso si falla un gate. La matriz real de navegador y la aceptación de la API de GitHub siguen siendo comprobaciones distintas.
