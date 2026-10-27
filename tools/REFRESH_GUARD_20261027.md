# Diagnóstico del candidato del 27 de octubre de 2026

Base del diagnóstico al iniciar: `origin/main` =
`977f5e2e331812310ef2a5852f33e47df6de7ad0`.
No se consultó la red ni se modificó el corpus. No acredita despliegue ni
recuperación del sitio vivo.

## Causa y registros

Los 734 registros de `developments.jsonl` se normalizan sin cuarentenas. El
airlock conserva además `FCMO-9E51A9966402` en `corpus/carried.jsonl`; se
retienen cinco registros retirados/tombstoned. El candidato admite 730
historias, con 730 pares completos por idioma nativo y cero pendientes. El
Story layer mantiene también sus avisos: 730 live, dos withdrawn y tres merged.
Los dos módulos rechazaban correcciones legítimas de evidencia por compararlas con
fotografías históricas. No faltan traducciones ni hay que producirlas para este
candidato.

| Prueba | Registro | Locale y campo | Diferencia legítima |
| --- | --- | --- | --- |
| `test_pd1_desk_values_and_airlock_baseline_are_preserved` | `FCMO-841949AEA161` | `es-419`, `zh-Hans`: `claims[7].label` | `DEMONSTRATED_THIRD_PARTY_EVALUATION_REPORT` pasa a `CLAIMED`, igual que en inglés; la prosa no cambia. |
| `test_matches_fixture_stories_on_derived_fields` | `FCMO-FAD9D0AFD3E4` | EN: `claims[0:7].qualifier`, `claims[5].label`, `claims[6].label` | Se retiran los siete qualifiers; las dos últimas etiquetas pasan a `NOT_ESTABLISHED`. Es la primera aserción fallida del módulo. |
| Mismo oráculo Story | `FCMO-841949AEA161` | EN: `claims[7].label`, `claims[7].qualifier` | Pasa a `CLAIMED` y desaparece `THIRD_PARTY_EVALUATION_REPORT`. |
| Mismo oráculo Story | `FCMO-49180A73A8A0` | EN: `claims[1,2,4,5,6,7,8].qualifier`, `claims[4,5,6,7,8].label` | Se retiran esos qualifiers; 4 y 8 pasan a `NOT_ESTABLISHED`; 5, 6 y 7 pasan a `CLAIMED`. |
| Mismo oráculo Story | `FCMO-7EBD0FA07C12` | EN: `claims[1].label`, `claims[1].qualifier` | Pasa a `CLAIMED` y desaparece `IN_MODEL`. |

Los campos Story son `evidence.claims`; arriba se usa la ruta del registro
canónico. Los índices son de base cero. El oráculo anterior se detenía en la
primera diferencia y ocultaba las otras tres identidades.

## Arreglo y regresiones

La importación y la taxonomía ya conservaban correctamente estas correcciones.
Cambiar esos productores para satisfacer la fotografía habría restaurado
certeza obsoleta. Se corrige la referencia de las pruebas:

- Se exige igualdad exacta de cada overlay histórico con el delta vigente cuando
  está admitido; sin delta o con una versión retenida se exige el valor previo.
  Se conservan las verificaciones de procedencia, valores del desk y cantidades.
- Se conservan las aserciones de identidad y metadatos históricos; todas las
  afirmaciones de los Story se comparan exactamente con la fuente admitida
  vigente. Una regresión sintética recorre una etiqueta extendida, `CLAIMED` y
  `NOT_ESTABLISHED` por importación ES/ZH y Story: verifica el qualifier, la
  prosa nativa, la completitud y la estabilidad de fecha/slug.
- La guarda conserva el primer bloque `FAIL`/`ERROR`, en vez de las últimas 25
  líneas. Publica el nombre de prueba y la excepción en la anotación de Actions
  y en `GITHUB_STEP_SUMMARY`, escapados y acotados. No publica frames ni logs
  arbitrarios; aplica los detectores de privacidad del airlock y oculta rutas.
  Si la aserción contiene muchos pasos exitosos, conserva el principio y el
  final de ese primer bloque para incluir también su causa anidada.
- Tres pruebas nuevas de diagnóstico fallaron antes del arreglo y pasan después.
  La batería también cubre errores de importación, salida sin unittest,
  parámetros privados de subtests y escape HTML/anotaciones. Reponer las
  afirmaciones históricas en los cuatro Story produce cuatro fallos y cero
  errores en la nueva comparación exacta.

## Reproducción sin red

Usar una copia Git local completa del mismo HEAD para preservar el historial de
primera publicación y evitar versionar archivos generados. `preflight` en la
base seleccionó `rebuild` (`CONTENT_AND_BUILDER_CHANGED`). Ejecutar los bloques
`run` de `.github/workflows/daily-refresh.yml` desde «Regenerate the canonical
public source from the corpus» hasta la guarda, en el orden del workflow:

1. `ingest_corpus`, `synchronize_relationship_surfaces` y la comprobación Python
   de igualdad de IDs de ingestión.
2. `sync_airlocked_locales`, `reconcile_locale_overlays`,
   `refresh_locale_identity`, `validate_localizations_partial`.
3. `public_research_desk --offline` y `visual_desk --offline`, con el resto de
   sus argumentos del workflow. Son las únicas adaptaciones funcionales al
   requisito de no usar red; no acreditan reabrir fuentes ni descubrir licencias.
4. `build_newsroom_surfaces`, `mark_pending_localizations`, `story_layer build`
   con `--history-git .` y validación de `stories.v2.schema.json`.
5. `newsroom_receipt finalize`, `build_final_release`, `build_ready_receipt` y
   `build_ready_receipt --check`, oráculo `verificar_traduccion`, `verify_release`.
6. `python3 tools/refresh_guard.py --tests`. Omitir instalación de pip: PyYAML ya
   está disponible. Usar `python3` donde el workflow usa `python`.

No ejecutar el paso de status-only, commit/push ni los jobs de producción.
La prueba completa es `python3 -m unittest discover -s tests`; las tocadas son:

```sh
python3 -m unittest tests.test_localization_completeness tests.test_story_layer tests.test_refresh_guard
```

`git diff --check` comprueba el diff del carril.

## Evidencia de aceptación

- Antes del arreglo, la guarda del candidato reconstruido rechazó exactamente
  `test_localization_completeness` y `test_story_layer`. Las pruebas focalizadas
  identificaron las diferencias de la tabla; no hubo fallos de ingestión.
- Después del arreglo, la reconstrucción vuelve a pasar las siete compuertas
  de `verify_release.py`: 730 completas y cero pendientes. El recibo corresponde
  al digest actual del builder. El módulo final de la guarda pasa 17 pruebas,
  cinco de ellas nuevas para el diagnóstico.
  El comando de las tres pruebas tocadas pasa 102/102, sin omisiones.
- `python3 tools/refresh_guard.py --tests` termina con salida 0 sobre ese árbol
  final reconstruido: los 39 módulos y las comprobaciones propias pasan. Quedan
  15 advertencias geográficas existentes (cinco valores en tres idiomas).

La suite completa usa copias Git aisladas, 118 módulos en procesos separados
con ocho workers y los dos módulos anidados de `tests.harness` (55 pruebas,
una omisión, incluidas en los totales). Las primeras ejecuciones agotaron el
tmpfs y se descartaron; estas aceptaciones usan `TMPDIR` en el disco de trabajo.

| Código | Archivos generados | Reportadas | Omisiones | Casos fallidos |
| --- | --- | ---: | ---: | --- |
| Base `977f5e2e3` | Versionados en la base | 1,286 | 10 | 3: Story histórico, journey timing, traducción HTTP |
| Parche `c42207be9` | Los mismos de la base | 1,292 | 10 | 2: journey timing y traducción HTTP, ambos también en base |
| Parche `c42207be9` | Reconstruidos | 1,292 | 9 | 0 |
| Final `06629bb0d` | Reconstruidos | 1,293 | 9 | 1: el mismo timeout HTTP de traducción de la base |

No hay casos fallidos nuevos. La quinta regresión diagnóstica explica la prueba
adicional del último renglón; la edición completa elimina la omisión condicional
por backlog del árbol no reconstruido.

Durante la ejecución, `origin/main` avanzó a
`c5629861d5bc795ca0ef18ef78d29b39a9b425f9`: añade `FCMO-0A0AF1D9853D` y estado
operativo, sin cambiar herramientas ni pruebas. Los cuatro commits del arreglo
se aplicaron limpiamente en otra copia Git de esa base. Su reconstrucción pasa
las siete compuertas: 735 registros actuales, 731 historias completas y cero
pendientes; las tres pruebas tocadas pasan 102/102, sin omisiones. La suite
completa de la tabla corresponde al snapshot inicial; esta comprobación adicional
se centra en la guarda dependiente de datos y las pruebas tocadas.
`python3 tools/refresh_guard.py --tests` también termina con salida 0 en esa
copia: 39 módulos, comprobaciones propias y los mismos 15 avisos existentes.
El digest del builder coincide con el del árbol del carril.

Incidencias y límites conservados:

- Se observó una carrera incidental en `test_publish_processes` al consultar
  un proceso que acababa de desaparecer (`ProcessLookupError`); la repetición
  aislada del módulo pasó 4/4. Está descrita en `NEEDS.md`, sin cambiar sus
  aserciones. No se usa esa repetición para ocultar el primer resultado.
- El recorrido de `test_studio_journey_timing` no recibe el ensayo del renderer
  bajo concurrencia, con el mismo error en base y carril. Se conserva como
  fallo compartido, sin relajar entrega, privacidad ni presupuesto temporal.
  `test_studio_translation` comparte un timeout HTTP seguido de error de
  limpieza del directorio de preview en ambas copias.
- La primera guarda sobre el candidato reconstruido terminó con un fallo del
  oráculo integral; su detalle quedó truncado. La ejecución directa posterior
  de `verificar_refresco.py` pasó: 731 historias incluyendo la sintética,
  EN/ES/ZH, descubrimiento y compuertas. No se atribuye una causa sin evidencia.
  Ese caso motivó conservar también el final del primer bloque de aserción.
- No se ejecutó publicación, despliegue ni navegador contra producción. Las
  advertencias de etiquetas geográficas existentes no se convirtieron en
  errores ni se cambiaron las guardas.

## CANON

Las rutas de esta tabla son relativas al Agent Hub. El informe del carril
conserva las rutas completas fuera del árbol público, conforme a `NO_MACHINE_PATHS`.

| Documento leído | Decisión concreta |
| --- | --- |
| `standard/CORE.md` | L2/L5: reproducir la ruta rebuild y distinguir candidato local de producción; no restituir evidencia obsoleta para satisfacer un proxy congelado. |
| `runtime/FCMO_RUNTIME_V1.txt` | Continuar hasta las aceptaciones autorizadas, sin atribuir recuperación al sitio vivo. |
| `AGENTS.md` | Cargar ingeniería y consultar la lección de Newsletter en `commons/red/DIGEST.md`; verificar el candidato mismo. |
| `disciplines/SOFTWARE_ENGINEERING.md` | Reproducir los dos rojos, localizar las diferencias por campo y conservar regresiones y comparación con la base. |
| `disciplines/VISUAL_ENGINEERING.md` | No cambió el arreglo: no se modifica diseño ni se declara inspección visual de producción. |
| `identity/README.md` | No cambió el arreglo: el carril repara guardas internas, sin redefinir la identidad de FCMO AI. |
| `identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt` | No cambió el arreglo: no se modifican marks, tipografías ni composición. |
| `identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt` | No cambió el arreglo: no se crean ni reinterpretan símbolos. |
| `identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md` | Diagnóstico en el job, sin trasladar maquinaria a la publicación. No se cambia atmósfera visual. |
| `disciplines/WORTHY_WORK.md` | NO_WORTHY_WORK: reparación interna de código y oráculos; no oferta, gasto, promesa comercial ni aprobación de publicación. |
| `identity/FCMO_EDITORIAL_SOCIAL_OS_v0.1.md` | No cambió el arreglo: el texto excluye explícitamente producto/ingeniería de FCMO AI; no se genera copia editorial. |
| `disciplines/COMMUNICATION.md` | Mostrar primera aserción útil y omitir trazas privadas; comunicar el límite local/producción. |
