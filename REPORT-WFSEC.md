# WFSEC — contención local verificada; aceptación pendiente

Fecha: 2026-10-04 UTC. Rama: `c5/wfsec`. Base pública local:
`3c9d25f61b7486b2757618ca590e9e6dcdd67ad4`.

**No está listo para integrar.** La contención de diagnósticos está probada, pero
faltan los SHA cotejados de las Actions. La suite completa conserva dos fallos
del nuevo control de referencias móviles. No hubo push, despliegue, consultas de
red, lectura de secretos ni borrado de ejecuciones históricas.

## Cambios

- Se elimina `backfill-arb-native-locales-once.yml`: era un auxiliar puntual;
  la búsqueda local no encontró un consumidor activo que justificara conservarlo.
  Desaparece su upload público incondicional de fragmentos y diagnósticos.
- Cada bloque shell de bridge y translation-health descarta stdout y stderr desde
  su inicio, incluidos errores de Git, lectura, copia y validadores. Desactiva
  tracing y emite únicamente un recibo numérico de salida. La sonda de integridad
  conserva códigos por comando y un número de fallos, sin preguntas, próximos
  pasos, identidades privadas ni texto recuperado de `SEAL_FAIL`.
- Los procesos Python y las sondas privadas reciben un entorno reducido y tienen
  cerrado el descriptor reservado a los recibos. No heredan canales de resumen,
  outputs o variables del runner. Los diagnósticos temporales usados para comprobar
  `SEAL_OK` se descartan; la limpieza final sigue siendo incondicional.
- El candidato sigue teniendo salidas suprimidas durante la verificación pública:
  un rechazo puede contener bytes aún no admitidos. Se conserva la cadena de
  seal, ratchet, linaje, SHA seleccionado, destrucción del checkout, verificación
  independiente, staging exclusivo de `corpus/` y promoción con reintentos.
- Translation-health queda restringido a `main`. Su construcción sigue fail-closed.
- El nuevo control recorre todos los workflows que identifican ARB, exige la
  supresión de cada paso, rechaza uploads/caches y canales públicos reabiertos,
  permite únicamente las tres Actions conocidas y exige SHA completo con versión
  comentada. También impide reintroducir el backfill.
- Se ajustan los contratos antiguos que exigían máscaras de SHA o mensajes
  derivados de diagnósticos; se conserva su cobertura de integridad/publicación.

## Evidencia

1. Commit rojo `4e90763`, autor `Codex <noreply@openai.com>`: prueba nueva ejecutada
   antes de cambiar workflows; 3 tests, 18 fallos por subcasos, 0 errores.
2. La versión final de esa prueba, contra los tres blobs locales de `origin/main`
   copiados a un directorio temporal sin modificar ninguna referencia: 5 tests,
   28 fallos por subcasos, 0 errores. Fallan tanto el control estático como la
   ejecución real de los bloques shell con herramientas sintéticas.
3. Los cuatro tests independientes de los pins pasan: ejecución sintética de los
   bloques reales en éxito, fallo, excepción y error de Git; sintaxis Bash de todos
   los bloques; retirada del backfill; mutaciones de echo/cat/tee, descriptor,
   tracing, resumen, outputs, artifacts y caches. Los marcadores sintéticos incluyen
   preguntas/próximos pasos, identidad de blob, comandos de workflow y una falsa
   línea `SEAL_FAIL`; no salen por stdout, stderr ni canales del runner.
4. `python3 -m unittest discover -s tests`: **72 tests; 70 pasan, 2 fallan,
   0 errores**. Ambos fallos corresponden exclusivamente a Actions sin SHA en
   bridge y translation-health. La aceptación solicitada aún no está satisfecha.
5. YAML de ambos workflows parseado localmente; inputs de Actions y Python
   comprobados. `git diff --check` pasa. No se añadió dependencia YAML al suite.

Para reproducir el contraste con `origin/main`, importar
`tests/test_arb_workflow_privacy.py`, copiar mediante `git show` los tres workflows
originales a un directorio temporal, asignar ese directorio a `WORKFLOWS` del
módulo y ejecutar sus tests con `unittest`. Las referencias originales permanecen
intactas; ningún proceso de fixture conecta con GitHub o ejecuta código ARB real.

## Continuación requerida

La regla común restringe la red al modelo salvo excepción del brief. Se pidió
autorización para consultas de solo lectura a GitHub de código y metadatos;
al cierre de este informe sigue sin respuesta. La búsqueda en repositorios y
notas locales no encontró pins verificables para estas Actions. No se inventaron
commits ni se degradó el gate para fabricar un verde.

Con esa autorización, resolver y cotejar los commits completos de
`actions/checkout@v6`, `actions/setup-python@v5` y
`actions/create-github-app-token@v3`; conservar cada versión en comentario,
verificar compatibilidad de los inputs y volver a ejecutar el suite completo.
Después Claude debe reejecutar fuera del entorno, antes de integrar. Push y
reactivación siguen siendo decisiones del operador. No se afirma que los
workflows deshabilitados en GitHub hayan cambiado de estado.

## Logs históricos: alcance de eliminación recomendado

Estos intervalos UTC son un barrido conservador desde la introducción de cada
workflow en el historial público local hasta la fecha de contención indicada por
el operador. Incluyen las versiones previas al diagnóstico GH-04 para cubrir
errores de Git y validadores. **No son un inventario confirmado de runs:** falta
cotejar metadatos, visibilidad y disponibilidad; no se leyeron logs ni artefactos.
El operador debe retirar también los artefactos del backfill dentro de su rango.
La eliminación no prueba ausencia de copias anteriores.

| Workflow | Rango UTC |
|---|---|
| Pull airlocked newswire with GitHub App | 2026-09-06 — 2026-10-04 |
| One-shot ARB native-locale debt digest helper | 2026-09-14 — 2026-10-04 |
| ARB translation source health | 2026-09-14 — 2026-10-04 |

Resumen: las rutas locales de fuga quedan contenidas y reproducidas con fixtures;
faltan los pins cotejados y la revisión histórica por metadatos. No integrar ni
reactivar todavía.
