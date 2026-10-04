# L2 — hotfix de marca

Rama: `c5/brand`, basada en `origin/main` (`d760a89`).

## Cambio

- Sustituí la marca interna prohibida por **FCMO** en las superficies públicas: interfaz `es-419` y `zh-Hans`, `release-src`, `scaffold`, páginas HTML, README y documentos de atribución, licencia y avisos legales.
- Aclaré el crédito como “Brought to you by FCMO” y “Con el respaldo de FCMO”. Se conserva la precisión legal existente: FCMO no se presenta como entidad jurídica separada y las funciones públicas no equivalen a cargos corporativos formales.
- Añadí `NO_FCMO_GROUP` a `tools/verify_release.py`. Revisa las fuentes públicas seleccionadas y la publicación ensamblada, con detección que ignora mayúsculas y admite espacios o tabulaciones. Los tres casos de regresión comprueban fuente, candidato y nombres permitidos.
- Reconstruí `release-overlay/final/` y `READY_TO_PUBLISH.md` para que los hashes congelados correspondan al nuevo `release-src`.

## Evidencia

- Red primero: antes de implementar el gate, `python3 -m unittest tests.test_no_fcmo_group` falló al no existir `check_no_fcmo_group`.
- `python3 -m unittest discover -s tests`: **67 tests, OK**.
- `python3 tools/verify_release.py`: **7/7 compuertas OK**, incluida `NO_FCMO_GROUP` sobre 563 archivos fuente públicos y el candidato ensamblado.
- `git grep -n 'FCMO Group' -- site release-src scaffold legal README.md ATTRIBUTION.md COPYRIGHT.md CONTENT_LICENSE.md LEGAL_REQUIREMENTS.md`: cero coincidencias (salida 1 de grep, que significa sin resultados).
- `git diff --check`: sin errores.

## Límite

Es evidencia local del candidato de release. No hice push ni verifiqué el sitio en producción; el despliegue y la inspección externa quedan para la revisión indicada por la campaña.
