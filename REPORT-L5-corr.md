# Campaña 5 — L5-corr: correcciones

Fecha: 2026-10-04 UTC. Rama: `c5/corr`, basada en `c5/v4`.

## Resultado

La página de correcciones ahora presenta los tres eventos con fecha, texto en el idioma correspondiente y enlace a una página de aviso localizada. Cada aviso muestra el titular afectado y el motivo; los dos casos fusionados también enlazan la historia vigente. Las rutas de aviso se sirven bajo `/corrections/story/` en EN, es-419 y zh-Hans, sin aparentar que son historias activas.

Los datos de las tres correcciones y `i18n/glossary.yml` ya estaban en la historia de PR #49 que precede a esta rama. Se verificó que `origin/pr/49/head` (`d8d9db8`) es antecesor de `HEAD`; no se duplicaron ni reescribieron esos datos.

## Prueba y cambios

- `e215994` añade primero la prueba contra el corpus real. Antes del arreglo falló porque la portada del ledger no incluía las tres entradas enlazadas.
- `4e3c3fa` añade las tarjetas localizadas, páginas de aviso para los registros retirados/fusionados y regenera `READY_TO_PUBLISH.md` con el generador de recibos.
- La prueba verifica tres entradas por idioma, el destino local de cada enlace y el texto localizado tanto en el ledger como en la página de aviso.

## Verificación local

- `python3 -m unittest discover -s tests`: **562 tests, 0 failures, 0 errors, 2 skipped**.
- Prueba específica `RealDataPaperBuildTests.test_corrections_are_linked_from_each_localized_ledger`: PASS.
- Recibo `READY_TO_PUBLISH.md`: PASS, **468 rutas**; las nueve rutas añadidas son tres avisos por cada uno de los tres idiomas.
- `python3 tools/build_final_release.py --check`: PASS.
- `python3 tools/verify_release.py`: **6/6 PASS**.
- `python3 tools/gates/run_all.py publish/l5-final`: **13/13 PASS**, incluido `NO_FCMO_GROUP`.
- `git diff --check`: PASS.
- El gate de glosario acepta 29 términos y emite 52 advertencias de términos evitados en prosa de origen ARB. El contrato las define como advertencias; no se modificaron traducciones ARB ni se debilitó el gate.

## Límite

No se hizo comprobación de navegador ni de producción. El build confirma el HTML estático y los destinos locales; no demuestra rendering visual en navegador ni despliegue. No hubo push ni cambios en otras ramas o worktrees. La suite completa, los gates y cualquier comprobación de navegador deben repetirse fuera de esta caja antes de integrar o publicar.

Resumen: las tres correcciones están enlazadas y localizadas en los tres idiomas; suite, recibo y gates pasan aquí. La confirmación del sitio en producción sigue pendiente.
