# Carril nl-newswire — la Newsletter no publica edición desde el 2026-10-24 11:52Z

Lee el Agent Hub: runtime/FCMO_RUNTIME_V1.txt, standard/CORE.md, disciplines/SOFTWARE_ENGINEERING.md y disciplines/HIGH_CONSEQUENCE.md. Lee AGENTS.md de este repo.

## Medido (2026-10-26 ~06:00Z)
- newsroom-status vivo: edition_date 2026-10-24 y airlock_generated_at 2026-10-24T11:51Z. Custos marca «newsletter-stale».
- El workflow «Pull airlocked newswire with GitHub App» (.github/workflows/newswire-bridge.yml) falla en el paso `verify`: OUT_VERIFY failure, run 40275447580.
  - El paso silencia toda salida (`exec 3>&1 >/dev/null 2>&1`) y sólo deja VERIFY_FAILED. La causa es invisible.
- `tools/newswire_bridge_partial_locales.py quarantine/verify` corre sobre `_public_release/`, que se genera desde ARB en el commit READY de `state/PUBLICATION_READY.json`. Ese commit hoy es 54eccad392ab7e796bd24d340f3f0fde3a74b04a.
- Clon completo de ARB, de sólo lectura: /var/tmp/kyrion-test/nw-repro/arb. Haz tu propia copia antes de modificar algo.

## Qué hacer (dueño: tools/newswire_bridge_*.py, sus tests y .github/workflows/newswire-bridge.yml; nada más)
1. Reproduce localmente los pasos del workflow sobre el commit READY: arma el `_public_release` exactamente como el workflow y corre quarantine y verify. Encuentra la causa exacta.
2. Arréglala en la causa.
   - Si un registro defectuoso bloquea toda la entrega, la cuarentena debe aislarlo; eso es lo que el propio workflow promete.
   - Nunca debilites una verificación de saneamiento ni de privacidad del airlock para que pase.
3. Haz visible la causa de un fallo de verify sin filtrar contenido privado: un código o motivo saneado en wire-status y en el resumen del job.
4. Agrega una prueba que se ponga roja si vuelve.

## Aceptación (reporte ≤10 líneas)
- Reproducción antes y después: el verify falla en el código viejo y pasa con el arreglo, sobre el release real del commit READY.
- La suite de tools del repo queda sin regresión.

Commit en español en fix/newswire-verify-20261026. Prohibido: push, secretos y tocar el clon de ARB.
