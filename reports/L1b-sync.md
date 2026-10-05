# L1b-sync — integración local de main en c5/v4

Fecha: 2026-10-05. Base v4: `a89c952`; main integrado: `78197c4`.

La integración conserva el lector v4, las protecciones WFSEC y los datos publicados de main. El candidato local contiene las rutas de las ediciones del 2026-10-03 y 2026-10-04 en EN, es-419 y zh-Hans. No se hizo fetch, push, publicación ni acceso a ARB. La revisión externa del arquitecto sigue siendo la frontera de promoción.

## Conflictos y resolución

Git produjo **89 conflictos**. La lista exacta está en [L1b-conflicts.txt](L1b-conflicts.txt).

| Grupo | Resolución |
| --- | --- |
| `.github/workflows/newswire-bridge.yml` | Se conserva el flujo v4: cadencia horaria, drills, preferencia por main sellado, fallback con ratchet, probe de cobertura, corpus guard, heartbeat y transacción optimista sobre corpus. Se aplican todos los SHA pins de WFSEC, restricción a main, supresión de stdout/stderr de cada shell, recibos numéricos, entorno limpio y cierre de descriptor 3 para los hijos Python/bash. Ningún texto arbitrario de `SEAL_FAIL` se convierte en código público. |
| `.github/workflows/translation-source-health.yml` | Se resuelve modify/delete conservando **exactamente** la versión endurecida de main. Complementa al probe del bridge. No vuelve el backfill retirado. |
| Canales del runner del bridge | Sólo se exportan rutas temporales fijadas por el shell y el booleano `stage`. La salida del guard se escribe primero en un archivo temporal; un `case` admite únicamente `true` o `false`. Los programas reciben un entorno sin canales `GITHUB_*` ni el descriptor público. La nueva prueba ejecuta el bloque real con salida maliciosa sintética y valores booleanos, inválidos y duplicados. |
| `CONTENT_LICENSE.md` | Se conserva el texto v4 que incluye fCMO y expresa la distinción entre marca y titularidad. Las diferencias de main eran formulaciones equivalentes de la marca FCMO. Las demás modificaciones legales/documentales de main se integran automáticamente. |
| `READY_TO_PUBLISH.md` | Se descartan los recibos incompatibles de ambas ramas y se regenera el recibo del lector estático v4 con `tools/build_ready_receipt.py`. |
| `REPORT.md` | Unión de informes anteriores, identificados como históricos, con el resultado de esta lane al principio. El informe WFSEC también permanece en `REPORT-WFSEC.md`. |
| `corpus/**` y ediciones | Main gana. Se comprueban **93 archivos del corpus** y **25 JSON históricos de ediciones** contra `78197c4`, byte por byte. Los contratos exclusivos v4 (`first-published.json`, tombstones y demás archivos propios) se conservan. |
| `ops/publication-desk/LEDGER.jsonl` | Aunque se fusionó sin conflicto textual, se reconstruye como append-union de líneas exactas de ambas ramas. El multiconjunto final es la unión de `a89c952` y `78197c4`: **63 líneas**, sin pérdida ni duplicación. Orden UTC comprobado por la suite. |
| `release-src/**` | Fuente de main como entrada; regeneración con las herramientas propias y el corpus actual. Se conservan las ediciones históricas exactas. Research y Visual Desk se ejecutan en modo `--offline`; sus recibos no afirman una reconsulta de fuentes en red. |
| `release-overlay/final/**` | Se reconstruye desde `release-src/` con `tools/build_final_release.py`: **193 archivos, 36 partes**. No se fusionan ni editan partes base64. Se retiran del índice las partes sobrantes de main. |
| `site/data/i18n/**` | Packs entrantes de main; se retienen los packs desk exclusivos v4, se reconcilian con el esquema publicable y se regeneran integridad y estado de traducción. Los catálogos legales se unen para conservar las claves de ambas ramas. Se añaden aliases de enums nuevos usando etiquetas curadas existentes y la etiqueta de Argentina. |
| `site/data/{stories,newsroom-status}*`, `site/news/**` | Se reconstruyen las superficies legacy, el Story layer v2, avisos de corrección, estado de traducción por campo y ACK con las herramientas v4. Los tombstones siguen mandando sobre una reaparición en el suministro. |
| HTML legacy de site | Se conserva el framing v4 de about/index/license/status; las superficies derivadas de noticias y sitemap se regeneran. El lector de Pages sigue siendo `tools/paper/build.py`. |
| `tests/test_no_fcmo_group.py` | Unión de las dos clases: pruebas del gate de publicación v4 y del gate adicional de `verify_release` de main. |

## Arreglos causales que necesitó la integración

1. **Ediciones sin historias nuevas.** El lector sólo generaba ediciones a partir de `url_date` de historias live, por lo que desaparecían las ediciones nuevas sin noticias aceptadas. La prueba roja se comprometió primero en `146bc93`. El Story layer ahora transporta `published_edition_dates`, derivadas de las ediciones publicadas del corpus; los snapshots de investigación sin autoridad de publicación quedan fuera de esa lista. Se mantienen los buckets históricos ya existentes del lector. El build genera páginas, navegación, tarjetas vacías honestas, Markdown, API JSON y redirects legacy, en los tres idiomas. No se inventan horas de publicación para ediciones sin historias.
2. **Inmutabilidad histórica.** El ingest filtraba `related_brief_ids` históricos por el conjunto actual de registros aceptados. Eso borraba dos referencias del 03-10. Una segunda regresión falló antes del arreglo y pasa después: una edición publicada conserva sus referencias públicas aunque un registro sea retirado o puesto en cuarentena más tarde. El oracle compuesto vuelve a coincidir con la regeneración completa.
3. **Pruebas acopladas al corpus anterior.** Los fixtures de carry/reinstatement/withdrawal necesitan una fuente válida y un huérfano realmente ausente; se construyen esas condiciones explícitamente. Las pruebas del corpus real ahora exigen los dos rechazos de fecha, además de los tombstones. Los recounts del recibo publicado se comparan con los IDs efectivamente publicados, y las pruebas de tarjetas distinguen ediciones con noticias y ediciones vacías. No se permite `event_at` nulo en el contrato v3.

## Evidencia local final

| Comprobación | Resultado |
| --- | --- |
| Suite completa `python3 -m unittest discover -s tests -v` | **595 pruebas; 0 fallos, 0 errores; 3 omisiones por navegador ausente** |
| Privacidad WFSEC, incluidos shell real y salida de guard adversarial | **6 pruebas, PASS** |
| `tools/verify_release.py` | **7/7 PASS**: las seis comprobaciones originales más `NO_FCMO_GROUP` de main |
| `tools/gates/run_all.py publish` | **13/13 PASS**, incluidos `NO_FCMO_GROUP`, `NO_MACHINE_PATHS`, `AGENT_LAYER` y comprobaciones de idiomas |
| `tools/validate_agent_hygiene.py --site publish` | PASS |
| Oracle del generador compuesto | PASS: corpus actual, crecimiento e idempotencia sintéticos |
| `reports/L1b-check.py` | **510 rutas**, **27 817 enlaces locales**, **0 errores**, **6 páginas de las ediciones nuevas**, **118 archivos de main preservados**, ledger exacto de **63 líneas** |
| Story contract v2 | PASS; 41 live, 1 withdrawn, 2 merged; 123 rutas de historias |
| Native editions publicables | 41 completas por locale; 24 `NATIVE_ARB`, 17 `MACHINE_REVIEWED`; 0 pendientes y 0 fallidas |
| Recibo estático | Release `newswire-a8ab11584169f896e64e2c0c`; 170 rutas por locale; SHA del candidato en `READY_TO_PUBLISH.md` |

El glossary gate conserva advertencias por términos de origen ARB; no se reescribe traducción fuente ni se rebaja el gate para ocultarlas.

## Límites que importan antes de promover

- **No hay Playwright/Chromium instalado aquí.** El oracle terminó con `BROWSER_UNAVAILABLE`. Las comprobaciones HTML, idioma, enlaces, Markdown y JSON de las seis páginas nuevas son prueba estática; no demuestran su aspecto visual. El arquitecto debe ejecutar la matriz 390×844 / 1440×900 en EN/es-419/zh-Hans y revisar los frames, overflow y consola.
- **Los dos registros nuevos permanecen en cuarentena:** `FCMO-045BB8282222` y `FCMO-5B5B447325A8` tienen `event_at: null` en main. Se conserva el suministro exacto y se exige `EVENT_AT_INVALID`. No se sustituye esa fecha por recorded_at ni por una fecha inventada. Las páginas de las ediciones nuevas existen, pero no representan dos noticias nuevas aceptadas en el lector. Sus snapshots históricos y referencias originales sí se conservan.
- **Estado de suministro pendiente de la ejecución real del bridge v4:** main no trae `corpus/wire-status.json`. El recibo regenerado conserva `TRANSPORT_DOWN` / `WIRE_STATUS_MISSING` y la superficie pública `DELAYED`; una release entrante o un rebuild local no fabrican un heartbeat exitoso. Tras promover, debe comprobarse el ciclo automático bridge → refresh → Pages → oracle en producción.
- La reaparición de `FCMO-FDBE3D996243` no anula su tombstone. Las tres correcciones siguen disponibles en los tres idiomas.
- Sin push, sin modificación de main/origin, sin otras worktrees, sin secretos y sin red. El merge local no es prueba de despliegue ni de continuidad productiva.

## Reejecución por el arquitecto

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_release.py
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --out publish --base /FCMO-AI-Newsletter/
cp i18n/glossary.yml publish/data/glossary.json
python3 tools/gates/run_all.py publish
python3 tools/validate_agent_hygiene.py --site publish
python3 reports/L1b-check.py
python3 tests/oraculos/verificar_paper.py publish
```

El último comando requiere `PLAYWRIGHT_MODULE` y Chromium ya instalados en el host. Los logs locales se conservan en `_audit/c5-l1b/`, excluidos de Git. El push corresponde al arquitecto/operador.

Resumen: main integrado localmente con WFSEC, ediciones y ledger conservados; lector v4 y gates verificables. Faltan la inspección visual en el host y la prueba del próximo ciclo real de publicación. Dos registros nuevos esperan una fecha de evento válida upstream.
