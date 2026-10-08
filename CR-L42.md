# CR-L42 — índice de búsqueda

Commit de implementación: `8c86448` (`c5/l42-search-index`, base `7c136d2`). Este informe queda en un segundo commit. Sin push.

Cerrado: filas de historias limitadas a `h,d,u,b,o,t`; desaparecen el resumen inglés duplicado y el vocabulario de agentes del índice del navegador. Historias recientes primero; ensayos listos conservan `kind/search_text` y se incluyen antes de fragmentar. Cada fragmento es un array JSON de hasta **153.600 bytes**, incluyendo UTF-8, comas y corchetes. El formulario enumera URLs; el cliente carga todas en paralelo, comparte/cachea la carga y permite reintentar fallos sin mostrarlos como búsquedas vacías. Agentes y documentos publicados apuntan a `api/v1/search-index.json`.

Se eligieron fragmentos para mantener la URL y forma del primer archivo sin limitar la cantidad de historias. Una fila individual superior al presupuesto sigue fallando explícitamente: no se recorta texto ni se omiten registros.

| Aceptación | Resultado observado |
| --- | --- |
| Build real, comando solicitado | PASS; 951 rutas; 90 historias por idioma, 0 filas de ensayo publicables |
| Fragmentos reales EN / ES / ZH | 1 / 1 / 1; 62.674 / 73.893 / 89.098 bytes; unión exacta de URLs |
| Corpus sintético, 1.000 historias por idioma | PASS; 5 / 14 / 9 fragmentos; máximos 153.229 / 152.663 / 153.296 bytes; 1 / 1 / 0 ensayos listos; formulario enumera todos |
| Cliente sin Chromium | PASS en EN/ES/ZH: último fragmento, carga paralela, caché, fallback de un archivo, texto del ensayo, escape HTML, reintento y consultas concurrentes |
| Pruebas nuevas | 5/5 PASS, 66,958 s |
| JavaScript generado | 1.183 bytes búsqueda; 3.172 bytes totales ≤ 30.720 |
| Suite completa | 831 pruebas / 905,231 s; 20 fallos, 4 errores, 4 omitidas. Base intacta: 780 pruebas / 556,109 s; 25 fallos, 23 errores, 4 omitidas |
| `python3 tools/verify_release.py` | FAIL heredado; 3/7 compuertas pasan, 4/7 fallan |
| `python3 tools/gates/run_all.py /tmp/l42-out` | FAIL `BINDING_COMPLETE`; evaluación independiente: 12/14 pasan, también falla `AGENT_LAYER` |
| `git diff --check` | PASS |

No cerrado: el overlay congelado conserva 50 historias frente a 90 en `release-src` (41 partes frente a 54 reconstruidas), el recibo conserva 618 rutas frente a 951 y falla la identidad/localización del candidato legado. `verify_release.py` reproduce los mismos bloqueos en un checkout intacto de `7c136d2`; ahora el chequeo del recibo sí logra construir y revela su desactualización.

No cerrado: `BINDING_COMPLETE` detecta `evidence — ` / `证据 — ` en la historia del 07-10 sobre agregadores de LLM. La salida parcial del build original de `7c136d2` reproduce el defecto EN sin cambiar el presupuesto. `AGENT_LAYER` detecta URLs inexistentes para `sil-ane`, `jos-alejandro-aguilar-l-pez` y `c-mara-de-diputados`; se reprodujo con el generador API original de `7c136d2` sobre las mismas rutas HTML de organizaciones, sin saltar aserciones.

No verificado: navegador real, OG por Chromium (`BROWSER_UNAVAILABLE`), despliegue/origen público y ciclos autónomos. Inspeccionados los formularios HTML finales en los tres idiomas y ejecutado el JS servido mediante Node. No se modificaron Studio, corpus, editorial, overlay ni compuertas.

<details>
<summary>Fallos restantes y evidencia en la base</summary>

Se ejecutó `python3 -m unittest discover -s tests` en esta rama y `python3 -m unittest discover -s tests -v` en un worktree intacto de `7c136d2`. Los **20** fallos siguientes aparecen por nombre en ambas ejecuciones (comparación exacta de encabezados `FAIL`):

- `test_story_layer.IngestSelectionTests.test_carried_record_is_published`
- `test_story_layer.RepositoryStoryLayerTests.test_cli_build_writes_a_valid_document`
- `test_localization_completeness.RealCorpusBacklog.test_committed_translation_status_is_truthful`
- `test_story_layer.TaxonomyTests.test_every_corpus_record_normalizes_to_record_v3`
- `test_localization_completeness.UICatalogs.test_every_reader_facing_enum_has_a_label`
- `test_localization_completeness.RealCorpusBacklog.test_health_reports_backlog_after_grace`
- `test_localization_completeness.RealCorpusBacklog.test_independent_recount_matches_committed_locale_backlog`
- `test_localization_completeness.RealCorpusBacklog.test_legacy_integrity_receipt_counts_field_level_backlog`
- `test_story_layer.IngestSelectionTests.test_mass_quarantine_refuses_the_batch`
- `test_story_layer.ShallowCheckoutTests.test_no_source_at_all_is_reported_not_invented`
- `test_story_layer.IngestSelectionTests.test_one_bad_record_is_held_back_alone`
- `test_story_layer.RepositoryStoryLayerTests.test_one_story_per_public_id_and_live_admission_census`
- `test_studio_integration.StudioIntegration.test_real_http_create_edit_preview_review_and_mock_publish`
- `test_studio_live.BareRemote.test_real_http_create_edit_preview_review_and_mock_publish`
- `test_story_layer.IngestSelectionTests.test_repository_corpus_publishes_every_admitted_id`
- `test_localization_completeness.RealCorpusBacklog.test_strict_validator_reports_incomplete_pairs`
- `test_refresco_diario.RefrescoDiario.test_todo_lo_publicado_tiene_ediciones_nativas`
- `test_localization_completeness.RealCorpusBacklog.test_translation_status_reports_real_backlog`
- `test_story_layer.TemporaryCorpusTests.test_unrecorded_duplicates_are_still_merged`
- `test_localization_completeness.RealCorpusBacklog.test_v2_overlays_follow_the_contract`

Los **4** errores son `test_publication_gates_pass_on_the_fresh_build`: dos subcasos (`publish`, `fresh`) de `test_v4_corpus_freshness.CorpusFreshnessBuildTests`, más `test_v4_front_freshness.FrontFreshnessBuildTests` y `test_v4_front_plan.FrontPlanBuildTests`. Todos fallan por `BINDING_COMPLETE`. En la base esas clases no llegan al método: su `setUpClass` falla por el presupuesto del índice. La prueba causal independiente es el mismo binding vacío en el HTML EN generado por el build original de `7c136d2`, comprobado con su propia compuerta; no se cambió `LIMIT`.

Ejemplos compartidos: `GRACE es-419=4 zh-Hans=3` frente al esperado `HEALTHY ...=0`; enum `reproduction_or_audit` sin etiqueta; `FCMO-B7F473626925` con `TIER_UNKNOWN`; CLI `live=90` frente a `live=91`. Los dos tests HTTP de Studio fallan en ambas revisiones: la base se detiene en preview (503), esta rama avanza hasta publicación y falla en comprobaciones locales heredadas.

</details>

Salida real: `/tmp/l42-out`; evidencias de esta sesión: `/tmp/l42-evidence/` (build, auditoría de índices, pruebas nuevas, suites, compuertas y comparación de base). Continuación: resolver los bloqueos heredados del release, repetir las compuertas y ejecutar el oracle de navegador en el host antes de desplegar.
