# Handoff — estado canónico de FCMO AI Newsletter

**Actualizado:** 2026-09-05  
**Estado de activación:** `AWAITING_GITHUB_APP_ONLY`  
**Sitio:** https://fcmo-ai.github.io/FCMO-AI-Newsletter/

Este documento sustituye como autoridad operativa al handoff del 2026-09-04. El texto histórico completo se preserva **sin borrar sus notas, diagnósticos ni lecciones** en [`docs/archive/HANDOFF_2026-09-04_pre_app_bridge.md`](docs/archive/HANDOFF_2026-09-04_pre_app_bridge.md).

Para el detalle exhaustivo del único paso externo restante y la lista DONE / PENDING / NOT STARTED, lee [`NEWSWIRE_ACTIVATION_STATUS.md`](NEWSWIRE_ACTIVATION_STATUS.md).

## 1. Estado real

La Newsletter pública, su newsroom autónoma, localización nativa EN/ES/ZH, frontends editoriales, release congelado, Pages, live oracle y health checks están construidos. Airlock v2 y las primeras ediciones nativas nuevas también están construidos del lado ARB.

El diseño anterior todavía hacía depender el primer round-trip de GitHub Actions dentro del repositorio privado ARB. Eso dejó de ser parte del contrato: `.github/workflows/newswire-bridge.yml` ejecuta los tests y el compilador de publicación de ARB dentro de un checkout privado **efímero** en el runner público de Newsletter usando un GitHub App read-only. La disponibilidad/facturación de Actions privadas ya no bloquea la Newsletter.

El bridge corre diariamente a **07:10 America/Mexico_City**, después de que la activación ARB de las 06:00 haya tenido su ventana esperada de ~50 minutos para aterrizar. La credencial sólo puede utilizarse desde el workflow revisado en `main`; el Client ID usa la interfaz recomendada actual de GitHub, el PEM sólo entra al token-minter, los diagnósticos privados no llegan al log público y un finalizador `always()` destruye cualquier residuo privado incluso en rutas de fallo.

## 2. Única acción manual restante

Configurar un GitHub App de lectura para ARB:

- instalarlo únicamente en `FCMO-AI/AI-Research-Breakthroughs`;
- permiso de repositorio **Contents: Read-only**;
- guardar su **Client ID** en la variable de Actions `FCMO_NEWSWIRE_APP_CLIENT_ID` del repo Newsletter;
- guardar su PEM privado en el secret de Actions `FCMO_NEWSWIRE_APP_PRIVATE_KEY` del repo Newsletter.

No hace falta PAT, `ANTHROPIC_API_KEY`, token publisher, App con permiso write, habilitar Pages, arreglar Actions privadas, ejecutar un workflow a mano ni configurar otro servicio para el launch contract. El PEM no debe pegarse en chat, source control, issues ni logs.

## 3. Qué ocurre automáticamente después

`Newswire Bridge → tests ARB → build/declassification determinista → _public_release → borrar checkout privado → verificador independiente → corpus/ → autonomous newsroom → locales → public research → visuals → Story/frontends → release gates → Pages → live oracle → production health`.

Un fallo en cualquier paso deja la release anterior viva y debe diagnosticarse como defecto concreto; no convierte automáticamente una nueva tarea técnica en requisito manual del usuario.

## 4. Frontera de seguridad

- ARB permanece privado.
- El GitHub App sólo puede leer ARB.
- La copia privada vive únicamente durante el paso de transporte y se elimina antes de staging público; un cleanup incondicional cubre también fallos tempranos.
- La identidad del commit privado y los diagnósticos de tests/build no se imprimen al workflow público.
- Sólo `_public_release` sobrevive a ese punto.
- `tools/newswire_bridge.py` vuelve a verificar digest/release identity, allowlist, IDs, ES/ZH, JSON/JSONL, secretos y marcadores privados después de borrar el checkout.
- Sólo `corpus/` puede ser escrito por el bridge en el Git público.
- El newsroom y el runtime público nunca reciben contexto privado de ARB.

## 5. Lo que no debe confundirse con launch work

ARB PR #31, la reconciliación histórica, está deliberadamente estacionada para después del primer round-trip. No es un faltante de Newsletter.

El problema general de runners/Actions privadas de FCMO-AI sigue siendo deuda de infraestructura útil de resolver para otros repos y para CI interno de ARB, pero **no es un prerrequisito de activación de Newsletter**.

## 6. Evidencia de finalización

No declarar la Newsletter completamente activada hasta observar el primer round-trip real con:

1. Bridge verde con pasos ejecutados;
2. `corpus/airlock.json` válido y content-addressed;
3. ACK del newsroom para esa misma identidad;
4. Pages verde;
5. live oracle verde;
6. las nuevas Story surfaces EN/ES/ZH visibles en producción.

Hasta entonces, el estado correcto es `AWAITING_GITHUB_APP_ONLY`.
