# L41 — admisión nativa y desbloqueo de publicación

## Resultado

Reparación local en `c5/l41-publish`, sin push. El árbol compuesto contiene
86 historias live con sus tres ediciones completas; Story v2 conserva además
1 retirada y 2 merges. Las cinco identidades con inglés residual quedan retenidas
con motivos explícitos en `release-src/data/publication-admission.json`.
El corpus recibido conserva el material para reparación y reintento automático:
backlog recibido es-419=4, zh-Hans=3, unión=5; backlog publicado=0.

La aceptación completa **no está demostrada**: falta Playwright/Chromium.
`ops/publish.py --check` termina con código 2 exactamente en el oracle de navegador,
después de suite, integridad, construcción, agent hygiene y los 14 gates verdes.
No se consultó ni modificó producción. El seguimiento autónomo real requiere
merge autorizado, deploy y ciclos posteriores observados por el verificador.

## Base y commits

El worktree ya existía sobre `79055f8` (L42) y el refresh público `2f7de90`.
`12168eb` ya había integrado L39, incluidos sus tres fixes; se conservó ese merge.

| Commit | Trabajo |
|---|---|
| `d540933` | Red first: vocabulario, hold/recovery y oracle antes del commit; 3 tests, 3 errores antes del fix. |
| `64d91be` | Red first: titular con evidence, binding vacío y rutas acentuadas; 3 tests, 1 fallo y 2 errores. |
| `01f8217` | Admisión, vocabulario, oracle independiente, etiquetas y corrección de gates; primera composición. |
| `5c977f0` | Refresh con ediciones reales de fixture; conservación de investigación pública en la composición. |
| `252892c` | Carry probado a través de ingest/sync/reconcile/ACK; tier preservado incluso con otro score. |
| `02c1531` | Overlay de recuperación sincronizado y su regeneración/check antes del commit automático. |
| `01440c4` | Oracle de publicación contra la versión inglesa comprometida; no confunde un update recibido con su carry. |

Todos los commits de L41: Codex <noreply@openai.com>. Ningún push, fetch ni cambio
a main/origin del repositorio de trabajo. Los remotes de pruebas fueron locales.

## Clases cerradas y decisiones

- **2 — tiers:** diez valores upstream, sus labels EN/ES/ZH y enums en los contratos.
  El tier procede del registro; una prueba recorre los diez con score=6 y conserva
  cada etiqueta. Useful vuelve a normalizarse y publicarse.
- **3 — tipos y labels:** `reproduction_or_audit`, `signal_or_leak` y `other`
  permanecen como tipos canónicos distintos: una auditoría y una señal no tienen
  la misma función informativa que un paper o un lanzamiento. Se renderizan labels
  naturales; se completaron también claim labels, regiones e idiomas observados.
  Tier y tipo se conservan como metadata opcional de Story y se muestran en sus facts.
- **4 — admisión:** ingest y Story usan la misma decisión por pares fuente/overlay.
  FAILED/PENDING retiene la versión recibida. Una versión previa se lleva adelante
  sólo si sus dos ediciones y bindings aún validan; sync conserva esos packs.
  ACK y salud de publicación juzgan el inglés efectivamente publicado;
  `--all-corpus` sigue midiendo la deuda de reparación recibida.
  Se ejecuta `verificar_traduccion.py` antes del commit. No se modificó ese oracle,
  el gate ENGLISH_LEAK ni se generaron traducciones de producción.
- **5 — oracle:** recuento independiente de hojas internas, comparación con inglés
  y detección de prosa inglesa; NOW deriva del corpus más grace+1h. Las assertions
  de receipts distinguen material recibido de historias realmente publicadas.
- **6 — gates/Studio:** BINDING_COMPLETE confundía un titular terminado en
  “evidence — FCMO AI” con un binding vacío. Se corrige la interpretación y se
  conservan negativos para labels vacíos, incluso separados por tags.
  API y lector ahora comparten slug Unicode para las organizaciones acentuadas;
  AGENT_LAYER valida los destinos. Los dos recorridos completos de Studio pasan.
- **Coherencia adicional:** apareció el overlay de recuperación de 50 historias
  frente a la fuente nueva de 86: tres compuertas de release fallaban. Se regeneró
  sin relajar hashes y se añadió su freeze/check al refresh. Pages sigue siendo
  el único renderer de producción y el único writer de despliegue.

Se conservaron los receipts públicos reutilizables para 85 historias admitidas;
la nueva historia recibió el pase offline. No hubo acceso externo a fuentes,
traducción, ARB privado ni secretos. L42 permanece: no cambios a search_index.py,
SEARCH_JS, presupuesto de búsqueda ni implementación de documentos llms.
La nota al origen está en [c5/CR-L41-upstream.md](c5/CR-L41-upstream.md): siete hojas
con fuga en cinco identidades. El snapshot examinado muestra claims[0].text y
technical.strongest_baseline también en zh-Hans; difiere de los summaries indicados
para esas dos identidades en el brief inicial. La nota refleja los bytes observados.

## Evidencia de aceptación

Logs locales ignorados en `_audit/l41/`; el verificador debe repetirlos en el host.

| Comprobación | Resultado |
|---|---|
| `python3 -m unittest discover -s tests` (ejecutado por ops --check) | 842 tests, 0 failures, 0 errors, 4 skipped; 769.433 s. |
| Desde tests: localization_completeness + story_layer + refresco_diario | 76 tests, OK; 59.041 s. |
| Native admission + gate corpus regressions | 7 tests, OK. |
| Tier/hold/recovery dirigidos finales | 4 tests, OK. |
| Carry con sync/reconcile/ACK | 7 tests, OK. |
| Workflow de recovery + admisión tras el cambio final | 29 tests, OK. |
| Oracle de localización publicado + admisión, cierre | 41 tests, OK; 2.870 s. |
| StudioIntegration + BareRemote, recorridos completos | 2 tests, OK; 201.413 s. |
| `verificar_refresco.py` | 87 historias; la sintética llega a EN/ES/ZH y discovery; oracle de traducción pasa antes del freeze. |
| `verificar_traduccion.py` sobre el árbol refrescado | 86 completas, pending=0; recientes materiales dentro del SLO. |
| `tools/verify_release.py` | 7/7, incluido NO_FCMO_GROUP; 86 registros y 0 traducciones pendientes. |
| `tools/gates/run_all.py` sobre candidato actual | 14/14; AGENT_LAYER y BINDING_COMPLETE pasan. |
| Paper | 906 rutas, 57 feeds, 596 redirects; JS 3172 B. |
| `ops/publish.py --check --out …` | Exit 2: BROWSER_UNAVAILABLE después de las comprobaciones anteriores. |
| HTML final de Useful y reproduction_or_audit | Seis páginas EN/ES/ZH contienen sus etiquetas en el texto del DOM; evidencia `dom-proof.json`. |
| Ready receipt, comprobación de cierre | OK, 906 rutas; candidato 8660fcb2638c. |
| `git diff --check` | Limpio. |

La suite general comenzó antes del último ajuste del workflow de recovery;
los 29 tests dirigidos posteriores cubren ese cambio, y las siete compuertas
verifican el nuevo overlay. No se presenta la ausencia de navegador como aceptación
visual. Las cuatro omisiones incluyen las pruebas que dependen de navegador/axe
no disponibles y el caso del renderer retirado cubierto por la integración real.

## Clase 6: alcance del diagnóstico visual y de Studio

No se cambió CSS ni el presupuesto móvil. El brief del host midió h1-top
EN/ES=296 px, ZH=299 px, dentro de max=460 y target=420. El oracle evalúa gates
además del viewport: el candidato inicial falla BINDING_COMPLETE por el titular
válido. Es un falso positivo del gate, no evidencia de un h1 demasiado bajo.
Las mediciones son del brief, no tomadas aquí. No hay screenshot local ni prueba
visual final: Playwright no resuelve. Debe ejecutarse el oracle móvil con
`--print-measurements` y conservar frames EN/ES/ZH en el host.

En un checkout coherente del commit inicial `12168eb`, Studio superó review/request
pero se detuvo al publicar por BINDING_COMPLETE. Aquí no se reprodujo el 409
pre-review del host bajo esas mismas condiciones. Los recorridos finales sí
alcanzan publicación local, incluidos revisión por la otra persona y repositorio
bare; no se afirma haber publicado en GitHub ni en el sitio público.

## Entorno y continuación

COMMON.md y los directorios de herramientas/temporal indicados en el brief no
existen en este entorno. No hubo permiso de filesystem para crear el temporal
solicitado. Se aplicaron las reglas comunes del mensaje. El primer discover
recibió ese TMPDIR inexistente y Python hizo fallback al temporal del sistema;
se corrigió después a `_audit/l41/tmp` dentro del worktree para las pruebas
restantes. Ese primer discover no es la prueba final de aceptación.

Continuación: con las herramientas del host, repetir el comando de aceptación
de ops del brief, comprobar los cuatro tests omitidos aplicables y el oracle
móvil/frames. Verificar el upstream note y ejecutar las suites sin flags que
omitan los oracles de refresh. Sólo el operador decide merge/push. Después:
Deploy, origen público y ciclos automáticos repetidos siguen pendientes.

**Resumen en español:** se reparó el vocabulario y la admisión por historia;
86 historias completas se construyen y cinco esperan reparación upstream.
Suite y gates pasan. Falta demostrar navegador y producción; no se hizo push.
