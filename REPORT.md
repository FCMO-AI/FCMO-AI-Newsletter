# Campaña 5 — WFSEC

La contención local de las salidas privadas está implementada y probada. El
backfill público está retirado. Los workflows restantes emiten únicamente códigos
de salida y conteos desde sus bloques shell.

**Aceptación pendiente:** `python3 -m unittest discover -s tests` ejecutó 72 tests:
70 pasan y 2 fallan por las referencias de Actions aún sin SHA cotejado. Se pidió
la excepción de red necesaria para consultar código y metadatos de GitHub; no hubo
respuesta ni acceso de red. No hubo push ni cambios en GitHub.

El commit rojo es `4e90763`, con autor `Codex <noreply@openai.com>`. La prueba final
también falla contra los tres workflows originales de `origin/main`: 28 fallos de
subcasos, 0 errores. Los cuatro tests independientes de los pins pasan con fixtures
de éxito, fallo, excepción y error de Git.

Detalles, límites, continuación y rangos conservadores de logs a retirar:
[REPORT-WFSEC.md](REPORT-WFSEC.md). Claude debe reejecutar antes de integrar.

Resumen: contención probada; faltan los SHA verificados. No integrar ni reactivar
hasta completar ese paso y obtener el suite entero en verde.
