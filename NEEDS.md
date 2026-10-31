# Integration requests from WP-B

## int4 Round 3 visual acceptance

The 65-unit extra-compact title step is calibrated from the reported five-line
Spanish headlines; the layout oracle now continues through every story, home
page, and Chinese route and prints the full set of failures. The deterministic
build/gates pass, but this sandbox blocks Chromium startup and loopback sockets.
On the integration runner, regenerate OG cards, rebuild the real-data candidate
with `--og-source`, then run `tools/gates/run_all.py`,
`tests/oraculos/verificar_paper.py`, and the relevant `browser/shot.mjs` capture
matrix. Review Chinese heading leading and all story/home headline/dek budgets,
plus the Spanish/Chinese local story-media variants in the final screenshots.

## Publication Desk / int2 follow-up

Resolved in int3: backlog tests now follow an independent recount at any backlog size. PD1 fields moved exactly into `part-desk.json`, with desk provenance and `MACHINE_REVIEWED` state; ARB import owns only its own packs. The validator, Story layer, translation status, integrity manifest and newsroom receipt now report the selected origin. The scheduled desk prompt still needs Claude's edit described in the integration handoff `codex/int3-desk-prompt-delta.md`.

## WP-B2 slot contract (deferred)

WP-B2 may add community integration only through the slots owned by the paper
template lane. It must not edit `community/ghost-theme/` or invent a second
Ghost client.

- `slot:subscribe`: a no-JavaScript-safe link to the Ghost portal signup. The
  link must remain useful when JavaScript is disabled and must not expose an
  email address or token in the static paper.
- `slot:cartas`: a best-effort rail of up to three published Ghost posts tagged
  `cartas`, ordered newest first. A timeout, 4xx/5xx, malformed payload or
  missing API key is a normal empty-rail result; the paper build remains
  successful and must not cache private/member data.
- `slot:banner`: reserved for the reader-facing edition/freshness banner. B2
  must not change its state or copy; it only places the already-localized
  banner emitted by A3b.

The paper-side adapter should receive `GHOST_CONTENT_URL` and
`GHOST_CONTENT_API_KEY` from its caller, use a bounded timeout (5 seconds),
and expose only `title`, `url`, `custom_excerpt`, `published_at` and an
allowlisted feature image URL. It must never call the Admin API.

## A3a/A3b integration points

- A3a owns `design/tokens.json`. `community/ghost-theme/build.sh` reads it
  when present and never writes it; the checked-in theme has a safe local
  fallback so the B1 lane remains independently buildable.
- A3b should call `tools/paper/pwa.py build --source <candidate> --out
  <candidate>` after static routes are generated, or perform the equivalent
  copy. The PWA manifest, service worker, icons and registration marker are
  expected at the candidate root, including `/favicon.ico`.
- The PWA service worker deliberately does not cache `data/newsroom-status`
  or any freshness/health document. A3b must not add a broad `cache.addAll`
  over the generated data tree.

## Operator boundaries

Ghost(Pro), real email delivery, domain/DNS, postal address and production
credentials remain blocked by the operator decisions in `OPERADOR.md`. The
implementation and tests in this lane use only the local `MockGhost`; no real
mail or external account is contacted.

---

# Integration requests from WP-A3

These changes are outside WP-A3 ownership and were not made here.

1. **WP-A4 / `pages.yml`: wire the OG stage into the publication build.** Run
   `tools/paper/og_image.py` into a temporary directory, then pass that directory
   to `tools/paper/build.py --og-source <dir>`. The SSG copies the validated cards
   to `publish/og/` and emits their PNG URLs in OG and JSON-LD metadata. Without
   this flag it deliberately keeps the existing local explainer as a valid
   fallback image.
2. **WP-C1 / approved legal copy:** provide the finalized locale content owned by
   `site-src/content/legal/**` and align its file interface with the SSG during
   integration. Until then, the generated privacy, license, and disclaimer routes
   state that approved legal copy is pending, and subscription remains inactive.
3. **Integration runner with browser/socket permission:** run the A3c PNG command,
   the browser harness, and the required `shot.mjs` matrix. This sandbox refuses
   both loopback sockets and Chromium startup, so no defensible screenshot sheet
   can be produced here. The operator visual decision O-14 therefore remains open.

---

# WP-A4 integration hand-off

These are cross-package changes A4 requires but does not own.

## A3b static generator

`tools/paper/build.py` must leave these exact source-of-truth files inside the generated tree:

- `data/stories.v2.json`: byte-for-byte copy of `--stories`;
- `data/newsroom-status.json`: byte-for-byte copy of `--status`.

A4 currently copies both files into `publish/` in `pages.yml` as a defensive bridge. The standalone gate command can validate route/locale parity from A3b's `data/routes.json`, but embedding the source files makes the candidate self-describing, enables field-provenance glossary enforcement, and is required before deployment identity is minted. A3b should therefore emit them directly; until then the workflow copy is fail-closed compatibility glue.

Canonical story pages are derived from `url_date` and `slug`; A4 verifies the exact three routes `YYYY/MM/DD/slug/`, `es/YYYY/MM/DD/slug/`, and `zh/YYYY/MM/DD/slug/`. Keep those paths stable. A `data-story-id="FCMO-…"` marker on each story `<main>` is recommended for stronger orphan detection, though path equality is already enforced.

Pending ES/ZH pages must contain the localized visible title (`Traducción pendiente` / `翻译待完成`) and must not render canonical English prose. This matches the current A3b draft.

## A1 daily refresh / integration owner

Before the new Pages workflow can run, the refresh transaction must produce and commit `site/data/stories.v2.json` by calling the A2 Story layer. It must then stop treating the retired overlay/release-src frontend as the Pages candidate. A4 did not edit `daily-refresh.yml`, which remains A1-owned under PLAN §4.1/W1.

The existing A1 test `tests/test_newswire_bridge_workflow.py::test_pages_candidate_gets_the_edition_banner_before_the_manifest_refresh` asserts the retired overlay pipeline. The integration-test lane should replace it with the A3b build → A4 gates → browser → deploy ordering already covered by `tests/test_pages_workflow.py`; A4 did not weaken or edit that foreign test.

## First LKG tag

Before enabling the new Pages deploy, create `lkg` at the commit currently proven live. Normal deploys fail closed if the tag is absent. The rollback job can rebuild either:

- a new paper release from a tagged commit containing `tools/paper/build.py`; or
- the pre-cutover legacy release with the tagged commit's own legacy assembler and gates.

After every successful public-origin identity check, `pages.yml` moves `lkg` to the verified source commit. Subsequent rollback never depends on an expired Pages artifact.

Do not remove the legacy assembler/overlay paths until `lkg` points to a live-verified paper release; they are the recovery mechanism for the first cutover. Once that condition is true, a later A4 cleanup may remove the legacy paths listed in PLAN §4.1.

## Release receipt

`tools/build_ready_receipt.py` still describes the legacy overlay. It is not invoked by the new Pages workflow. Replace it with an SSG receipt only after A3b's final route/data manifest lands; doing that earlier would either encode a guessed interface or break the still-running refresh transaction.

---

# INT2 integration resolution (2026-09-26)

The A3/A4 seams above are now closed on `wp/int2`:

- A3 embeds byte-identical Story/status inputs, marks every story `<main>` with
  `data-story-id`, copies referenced local story media, and emits the final
  `data/routes.json` contract. Pages no longer performs defensive data copies.
- Pages generates OG cards in runner-temporary storage and passes them to A3
  with `--og-source` before the ten A4 gates and browser oracle run.
- Daily refresh explicitly calls the A2 Story layer and commits
  `site/data/stories.v2.json`; it no longer assembles the overlay as the Pages
  candidate. The obsolete edition-banner ordering test now asserts the real
  Story layer → A3 build → A4 gates → browser → deploy transaction.
- The readiness receipt measures the A3 route manifest and its embedded Story
  and newsroom-status artifacts; it no longer mounts or describes the legacy
  overlay frontend.
- Real-data regressions cover canonical English headlines, localized pending
  pages without reader-visible internal IDs, translated-field preservation,
  structured proper names, local media resolution, and broken-reference/internal-ID
  gates.

The **First LKG tag** operator boundary remains open. The legacy assembler and
overlay files are intentionally retained as the first-cutover rollback path
until a paper release is browser-verified, deployed, live-verified, and advances
`lkg`. Chromium/loopback-dependent OG and browser evidence must be produced by
the integration runner with those permissions.


## Playwright runtime configuration (int5)

The browser scripts first use `PLAYWRIGHT_MODULE`, then resolve the repository's
`playwright` Node package. This server should export `PLAYWRIGHT_MODULE` from its
external runner configuration; do not commit a machine-specific path. CI installs
Playwright 1.63.0 and Chromium into runner-temporary storage.

## Lane int6 favicon note

- The existing PWA artwork is SVG. Generated pages reference `favicon.svg` and the existing 192px SVG as the Apple touch icon. No repository tool generates a 180px Apple touch PNG; producing one would require adding a rasterization dependency, so this lane keeps the existing icon artwork and formats.

## v2 lane v1 handoff

- **s1:** The temporary `subscribe_block(zone, locale)` adapter has been replaced by s1's component. Verify the integrated landing and subscribe page at both Ghost states.
- **p2:** The landing's `#start-here` path gives a plain-language choice between letters, technical evidence and method. The Newsletter section still needs its owned letter, beginner-guide and community page redesign.
- **p1:** Apply the technical page blueprints in `DESIGN_V2.md` to interior pages. The current story screenshot demonstrates the shared shell but the long-form body still has the earlier visual treatment.

---

# Integration needs from lane s1

- The v1 landing calls `tools.paper.templates.subscribe.subscribe_block(zone, locale)` for the FCMO Group section. The technical section still needs its own subscription placement in p1.
- The production Pages build needs `GHOST_URL` as a build variable only after the Ghost staging matrix and legal/domain decisions pass. The current `tools/paper/build.py` reads `GHOST_PORTAL_URL`; `community.render_subscribe` also reads `GHOST_URL`, so the build works without an out-of-lane edit. For a later cleanup, replace `self.portal_url = os.environ.get("GHOST_PORTAL_URL")` with `self.portal_url = os.environ.get("GHOST_URL") or os.environ.get("GHOST_PORTAL_URL")`.
- Ghost's exact Portal newsletter choice controls, Mailpit magic-link markup, Admin API newsletter create/update schema and per-newsletter welcome-template support require the staging run. They are not verified in this sandbox.
# Lane a1 dependencies

No out-of-ownership edits are currently required.

The implementation does not emit a `/.well-known/security.txt`: the repository has no verified security contact. No other applicable well-known standard was identified for the static agent API.

## v3 lane n1: public brand boundary for n3 and integration

The new `NO_FCMO_GROUP` gate deliberately fails until these reader-facing files owned outside n1 are corrected. Do not narrow the gate to make it green.

- **n3 / agent API:** In `tools/agent/build.py`, change the `llms.txt` / `llms-full.txt` introductory sentence to say the umbrella is **FCMO**, the human newsletter is **fCMO / Javier**, and the technical daily is **FCMO AI / Matías**. Change `agent.json` `publication.brands` to `umbrella: FCMO`, `newsletter: fCMO`, `technical_paper: FCMO AI`; change `publication.zones` to `FCMO landing`, `fCMO Newsletter`, `FCMO AI technical paper`. These fields currently emit the forbidden internal name into every build.
- **n3 / email and community:** In `tools/email_render.py`, replace the letter email masthead with `fCMO · {LETTER_NAME}`. In `community/config/subscriptions.json`, set `products.letter.brand` to `fCMO`. In `community/config/member_messages.es.json`, sign the confirmation `Javier, fCMO`. In both `community/ghost-theme/partials/subscription-choices.hbs` and `.hbs.in`, replace the internal umbrella label with `FCMO` and the Javier section label with `fCMO · Javier`. Update `tests/test_subscribe_v2.py:test_letter_preview_uses_brand_and_ghost_account` to assert `fCMO` in the rendered email: this is the authorized brand contract change, not a test relaxation.
- **integration / legacy public sources:** Replace the internal name in `release-src/index.html`, `scaffold/release-index.html`, and `site/{about,disclaimer,license,privacy}.html`, including JSON-LD organization name, meta/header/footer, and legal notices. In `site/data/i18n/{es-419,zh-Hans}/ui.json`, replace the name in both source keys and translations, then verify translations remain semantically accurate. The legal source `CONTENT_LICENSE.md` and any derived public legal copy should describe FCMO as the umbrella without implying a legal entity or changing authorship. These files are outside n1 ownership.
- **integration / official build:** Rerun the real-data build and `tools/gates/run_all.py`. The gate currently finds 10 built agent/llms occurrences and the source files above. Review `NO_FCMO_GROUP` together with existing legal and localization gates before release.
# n2 integration needs

## Shared page CSS from n1

The n2 templates now emit editorial structure that needs matching rules in the shared `site-src/assets/css/paper.css` owned by n1. Please add scoped styles for:

- `.front-ledger`: a compact, readable data strip for live stories, tracked topics and organizations.
- `.story-hero`: keep the lead illustration inside the reading column; maintain a deliberate aspect ratio and avoid creating an empty grid row beside the story body.
- `.archive-item`, `.archive-art`, `.archive-art img`, `.archive-copy`: use desktop columns around `8rem minmax(8rem, 12rem) minmax(0, 1fr)` for date / fixed thumbnail / readable copy, with a clear stacked layout on mobile. Keep thumbnails cropped to a consistent ratio.
- `.archive-totals`, `.archive-meta`, `.taxonomy-neighbors`, `.taxonomy-neighbors ul`, `.taxonomy-neighbors li`: compact corpus summaries and co-occurrence links.
- `.edition-neighbors`, `.related-reading`, `.story-taxonomy`: visible, keyboard-friendly navigation with clear separation from article evidence.
- `.method-steps`, `.method-example`: make the process scannable and the linked live example distinct.
- `.status-grid` with four status cards: use the available width without leaving a lone fourth card at desktop; collapse cleanly at narrow widths.

The final capture covered eight page types in all three locales at 390px and 1440px: 48 screenshots, zero console errors. The story hero now sits in the reading column and archive stories carry their editorial art. Screenshot review shows the existing archive grid makes its image column too wide and compresses the copy; use the column sizes above. Please finish the shared styles for the corpus strip and navigation too, and balance four status cards at desktop.

The captured shared shell still shows `FCMO Group` in reader-facing navigation and the masthead. This belongs to n1: replace it everywhere with the approved FCMO / fCMO / FCMO AI architecture, then add and run the `NO_FCMO_GROUP` gate over all three built locales and reader-facing source strings. The current 12-gate result predates that gate and does not establish brand compliance.
---

# Cross-lane changes needed for Newsletter v3

The n3-owned community, email, and agent surfaces now use FCMO, fCMO, and
FCMO AI. The following reader-facing strings are in `tools/paper/**`, owned by
n1 or n2; n3 did not edit them.

1. In `tools/paper/templates/layout.py`, replace the masthead and zone-switch
   label `FCMO Group` with `FCMO` for the umbrella and `fCMO` for Javier's door.
2. In `tools/paper/templates/subscribe.py`, replace `FCMO Group` in EN, ES, ZH
   descriptions and the section kicker with `fCMO` for Javier and `FCMO` for the
   common umbrella.
3. In `tools/paper/templates/landing.py`, replace `FCMO Group` in all three
   locale copy maps and section kickers: use `FCMO` for the site entry and
   `fCMO · Javier` for the letters section.
4. In `tools/paper/build.py`, change both root page titles from `FCMO Group` to
   `FCMO`, their descriptions to `fCMO Newsletter and FCMO AI technical paper`,
   and the 404 title/header/footer to `FCMO` with the two named divisions.
5. In `tools/paper/redirects.py`, update the comment describing the locale
   roots to the FCMO landing. This is source only, but prevents future drift.

The existing built site still contains the unofficial term until those changes
are integrated. The n1 `NO_FCMO_GROUP` gate should catch any remaining copy.

## Screenshot review of the current n3 checkout

The 390/1440 EN/ES/ZH landing and Diario screenshots in the n3 queue have zero
console errors. Against the Semafor mobile and Platformer desktop references,
the paper has strong type and useful story density, but the fCMO landing still
uses a text-only "Latest letter" empty state as its visual anchor. The
subscription area is dominated by a coming-soon panel. Javier's artwork was
not present in the inbox at this review, so its visual language remains
unassessed. N1 should use the new artwork if it arrives, place real letters or
guides in the opening fCMO area, and recheck the 390/1440 screenshots after
replacing the old brand strings. The red delayed-edition banner is truthful to
the current data and should stay until fresh production evidence exists.

`READY_TO_PUBLISH.md` still describes the September 10 v4.1.1 release and its
old route count. The integrator should regenerate that receipt only after the
v3 candidate, its gates, browser matrix, Pages deployment, and public-origin
verification are complete; a local build cannot truthfully update it.

## L40 — activación de Studio en el host

- **Dónde:** `OPERATOR-LINE.md`, unidad `ops/studio/fcmo-studio.service` y el
  entorno privado del usuario `fcmo-agent`.
- **Qué falta y por qué:** esta sesión devuelve `offline` para el gestor systemd
  de usuario y no tiene el socket local de Tailscale. El mandato reserva la
  instalación y el mapping al operador; no se instalaron desde esta lane.
- **Cambio exacto:** preparar el entorno 0600 con el origen
  `https://fcmo-hub.tail8cbe0b.ts.net:8447`, listener `127.0.0.1:8490`, datos privados
  fuera del checkout y ambas cuentas locales. Ejecutar desde la raíz del checkout:
  `python3 ops/studio/host.py --install && tailscale serve --bg --https=8447 http://127.0.0.1:8490`.
- **Prueba pendiente:** login y guardar/recargar un ensayo por ese HTTPS en
  escritorio y teléfono; confirmar TLS/ACL, acceso de Javier y persistencia de
  la unidad. La prueba de loopback usa cuentas temporales y no reemplaza ese paso.
- **Publicación pública:** conservar dry-run hasta demostrar las dos identidades
  personales de GitHub, protecciones, backup y el recorrido PR/Pages/origen live
  descrito en la activación existente. No añadir bypass humano ni cambiar gates.

## L40 — renderer bloqueado por el corpus actual tras integrar main

- **Dónde:** `tools/paper/search_index.py:43`, llamado por
  `tools/paper/build.py:856`. El código es idéntico a `origin/main` en `f683aa2`;
  estos archivos del generador no se modificaron en la lane de Studio.
- **Qué y evidencia:** los 68 stories live del corpus actual producen índices
  de EN=166155, ES=187049 y ZH=205362 bytes; los tres exceden 153600 bytes.
  El build aborta y las vistas previas reales responden 503. La suite Studio
  tiene seis casos afectados, incluyendo publicación bare e identidad byte
  por byte. La prueba anterior con el corpus de `9468c9e` no acredita este estado.
- **Cambio requerido del dueño del generador:** compactar la serialización del
  índice para el corpus real y su crecimiento, resolviendo la duplicación de
  campos de búsqueda humana y compatibilidad de agentes. Conservar los 150 KiB,
  cobertura de todos los stories, locales y contratos de consumidores. No subir
  el límite, quitar stories ni cambiar las aserciones para hacer pasar la suite.
  El diseño concreto de compatibilidad debe resolverlo la lane del generador.
- **Reproducción y aceptación:** ejecutar
  `python3 -m unittest tests.test_studio_preview tests.test_studio_integration tests.test_studio_live tests.test_studio_translation tests.test_studio_email_seam`
  y el build real de `tools/paper/build.py` con Story/status actuales. Después
  repetir toda la suite Studio y el recorrido del launcher con navegador.

## L40 — Chromium disponible para repetir la batería actual

- **Dónde:** configuración externa del runner de Playwright. El módulo de Node
  acordado existe; su Chromium headless build 1243 no está montado en esta sesión.
- **Cambio exacto:** montar el ejecutable existente y configurar `CHROME_PATH`
  con su ruta, o montar el cache completo y configurar
  `PLAYWRIGHT_BROWSERS_PATH`. No instalar dependencias desde esta lane.
- **Aceptación pendiente:** repetir `tests.harness.studio_host_journey` después
  de reparar el renderer; las 46 imágenes existentes son de la ejecución previa.
  Los recibos actuales registran `completed: false` y no acreditan esas imágenes
  para el corpus nuevo.


## Studio ready — continuación fuera de esta lane

- **Renderer canónico:** `tools/paper/build.py`, `PaperBuilder._topic_links`.
  Trasladar el índice de membresía por historia y el caché de vecinos de
  `studio/server/render_preview.py:StudioPaperBuilder` al builder común;
  conservar duplicados por historia, exclusiones nombre/slug, orden de empates,
  límites y todos los bytes de salida. Actualmente Studio lo acelera, pero las
  compilaciones de publicación generales todavía recalculan ese índice. Esta
  edición está fuera del alcance studio/ de la lane. Verificar con el test de
  identidad completa y los gates del renderer; luego retirar sólo el override
  redundante de Studio. No se ha cambiado el renderer canónico en esta lane.
- **Aceptación visual:** montar las dependencias existentes de Playwright y
  Chromium del runner, sin descargas en esta lane. Ejecutar
  `python3 -m tests.harness.studio_host_journey --out "$STUDIO_EVIDENCE"`
  con salida privada; exigir completed=true, frames actuales de escritorio y
  teléfono, y tiempos cold_preview_seconds/preview_timeout_ms en journey.json.
  En esta sesión el probe devuelve BROWSER_UNAVAILABLE: Playwright ausente.
  Los frames históricos no prueban este bundle. Repetir después el arranque en
  el host autorizado de Javier y medir allí la primera vista previa; esta lane
  no inicia ni reinicia servicios reales.
- **Pruebas web completas:** montar una instalación que respete
  `studio/web/package-lock.json` en `studio/web/node_modules` y repetir
  `npm test --prefix studio/web`. docmodel no se pudo ejecutar porque falta
  prosemirror-model; login y WebP pasan sin esas dependencias. Con esbuild
  disponible, repetir también `node studio/web/build.mjs` y bundle_ready.
  La lane conserva el lockfile y no instala paquetes ni descarga dependencias.

# Studio: reconstrucción e inspección pendientes

- Dependencias existentes de `studio/web/package-lock.json` no disponibles en
  este entorno. `npm ci --offline --ignore-scripts --no-audit --no-fund` falla
  con `ENOTCACHED`; `npm run build` falla por ausencia de `esbuild`.
- Cambio necesario en un entorno con esas dependencias: ejecutar en el checkout
  limpio `cd studio/web && npm ci && npm run test && npm run build`; comprobar
  desde la raíz `python3 -c 'from studio.server.bundle import ready; assert ready(".")'`
  y conservar los artefactos y manifiesto generados. El bundle comprometido sigue
  siendo el anterior; la comprobación de integridad rechaza las fuentes nuevas
  hasta reconstruirlo. No reiniciar Studio sobre el checkout nuevo antes de ese paso.
- Fallos nuevos mientras el bundle siga obsoleto:
  `SingleURLHost.test_preflight_requires_both_local_logins_before_installing` y
  `SingleURLHost.test_probe_reads_real_loopback_chrome_assets_and_auth_boundary`.
  Ambos deben pasar después del build; no cambiar sus afirmaciones ni el guard.
- Chromium tampoco está disponible. Inspeccionar el flujo de autor y las
  superficies de suscripción en los tres idiomas a 390 y 1440 px, teclado,
  estados ocupado/error/pendiente y textos largos. Los templates y pruebas DOM
  no acreditan esa inspección visual.
- La política de esta ejecución prohíbe red, llamadas reales a modelos, correos
  reales y reinicios de servicios. Comprobar en el host la sesión Codex por
  suscripción, doble opt-in y baja de Kit, preferencia de idioma, recepción real
  y persistencia tras reinicio. El procedimiento público está en
  `docs/STUDIO-SINGLE-SOURCE-DEPLOY.md`.
- El centro de preferencias para cambiar a un solo idioma y separar diario,
  piezas, resumen semanal y alertas no existe todavía. El estado actual conserva
  las membresías explícitas por formulario; puede haber más de un idioma por persona.
- Inspección de código: al salir de `studio/web/src/screen-editor.js`, el dispose
  cancela `figT`/`srcT` y solo conserva el documento. Una edición de recursos aún
  pendiente puede perderse al navegar antes del debounce. Cambio necesario:
  esperar/guardar documento, figuras y fuentes antes de Publicar o cambiar de
  pantalla; conservar los buffers y la pantalla cuando falle la escritura.
  Reproducir con navegador: cambiar el pie de figura y pulsar Publicar antes de
  900 ms; comprobar el recurso guardado y la regeneración en ambos idiomas.
  Esta transición de UI sigue pendiente; el flujo HTTP no acredita ese recorrido.

# nl97-fix

La aceptación completa requiere un host con pytest y Playwright/Chromium ya instalados. Esta caja no dispone de ellos y el carril no autoriza red ni dependencias nuevas.

Ejecutar las seis regresiones sin cambiar sus aserciones:

```sh
nice -n 15 python3 -m pytest -q \
  tests/test_corpus_guard.py::RepositoryTombstonesTests::test_recorded_quarantine_is_carried_but_not_a_failure \
  tests/test_native_admission.py::NativeAdmission::test_softbank_source_claims_are_classified_and_admitted \
  tests/test_story_layer.py::IngestSelectionTests::test_mass_quarantine_refuses_the_batch \
  tests/test_localization_completeness.py::UICatalogs::test_spanish_catalog_is_spanish \
  tests/test_localization_completeness.py::RealCorpusBacklog::test_pd1_desk_values_and_airlock_baseline_are_preserved \
  tests/test_paper_build.py::PaperBuildTests::test_machine_prepared_story_discloses_review_status_and_english_original
```

El deploy ejecuta `nice -n 15 python3 tools/unittest_shards.py --index N --count 8`, para cada N de 0 a 7. La partición local cubre las 993 pruebas descubiertas una sola vez; listar la partición no equivale a ejecutar esos ocho grupos.

Ejecutar `nice -n 15 python3 ops/publish.py --check --tests-prevalidated` después de los ocho grupos, y `nice -n 15 python3 tests/oraculos/verificar_paper.py publish` sobre el candidato producido. Confirmar que el primer comando termina después de `GATES PASS (14/14)` y que ambos dejan cero procesos de servidor, Node o Chromium. Las pruebas locales reproducen y corrigen fugas al terminar, al vencer el plazo y entre watchdogs anidados, pero no sustituyen esta comprobación con Chromium real.

Comparar la duración por comando con ejecuciones recientes de main y con el run 39208638359. El código sitúa el oráculo de navegador inmediatamente después de las catorce compuertas; la suite serial anterior y los builds repetidos precedían a ese punto. Sin consultar los logs de Actions no se atribuye una duración exacta a un comando concreto. Los tiempos versionados de clases lentas suman 15126 segundos; no son una medición nueva del run afectado.

La ejecución integral local fue interrumpida después de unos 390 segundos en `tools/build_ready_receipt.py`, al estar confirmada la ausencia del navegador necesario para la aceptación posterior. No dejó procesos descendientes vivos ni cambió el recibo. La ejecución directa del oráculo confirmó `BROWSER_UNAVAILABLE`. No se probó publicación, despliegue ni frescura del origen público.

# paper-perf

La suite completa encuentra un bloqueo heredado en
`tests/test_ready_receipt_pipeline.py:53`,
`ReadyReceiptPipelineTests.test_local_check_prepares_a_receipt_before_the_integrity_gate`.
El fixture parchea `publish.subprocess.run`, pero `ops/publish.py` ya ejecuta
los comandos mediante `publish.run_command` (que usa `Popen`). La prueba lanza
una nueva discovery real, que vuelve a ejecutar esta misma prueba. Esto impide
terminar la aceptación completa y puede alcanzar la preparación real del recibo.

Cambio exacto fuera de los archivos de este carril: sustituir únicamente
`mock.patch.object(publish.subprocess, 'run', side_effect=run)` por
`mock.patch.object(publish, 'run_command', side_effect=run)` en ese fixture.
Conservar todas las aserciones de orden, número de llamadas y resultado.
Después ejecutar esa prueba y `nice -n 15 python3 -m unittest discover -s tests`
sin exclusiones. El problema existe en la base de este carril; el renderer no
causa la recursión. La ejecución recursiva local se detuvo y no se acredita como
una aceptación verde de la suite completa.

La sustitución propuesta se comprobó cargando una copia de la prueba en memoria:
sus aserciones originales pasan en 0,006 s y el archivo versionado permanece
intacto. También se interceptó `Popen` antes de crear hijos: el fixture original
intenta lanzar `python -m unittest discover -s tests` pese a su mock.

# studio-github-connect

Outside this lane's ownership, rebuild the tracked Studio bundle and offline seed
from the updated `studio/web/src/**`: `studio/web/dist/**` and
`studio/web/offline/{app.seed.js,screens-home.seed.js,seed-manifest.json}`.
The local checkout has no `esbuild`; the offline fallback intentionally rejects
these source changes, and `npm run build` removes `dist/` before that rejection.
Run `npm run build` and `node refresh-offline-seed.mjs` in an environment with
the repo's already-locked esbuild available, then commit those generated files
with the source lane. Do not install dependencies or run the destructive fallback
in this lane.

## Lane V (visual)
- Lane T: `verificar_paper.py` front block still filters `kind === 'front'` (home-pages=0). Retarget to `landing` (`.cover h1`, bottom of `.cover-evrow` < 900 at 1440; lines <= 4). With lane V's CSS this holds in en, es-419, zh-Hans at 1280/1440/1920.
- `tests/test_no_frozen_corpus_counts.py` fails on c6/integration (not caused by lane V): front-page story count is now 300 and four tests contain a literal `300` (`test_clock_boundaries.py:48`, `test_localization_completeness.py:43`, `test_v4_visual_width.py:48`, `test_wire_liveness.py:72`).
- Search placeholder text could not be shortened in CSS; the field now sits on its own row at <= 520 px so the full text shows.


## Studio L1 (publish-robust) needs from other lanes

- `studio/server/credentials.py` (GitHubCLI): `identity()` is overridden there; L1 adds `GitHub.account()` which reuses `call()` when present, so the author's numeric id is available for the noreply commit email. Nothing to change unless you want a native override.
- `studio/server/publish.py` (CLI dry run) still calls `Workspace.verify_base` (strict equality, kept unchanged) and `protected()`. For the dry run to mirror the new flow it should call `verify_confined` and respect `STUDIO_PROTECTION_MODE`.
- `studio/server/http.py`: no API to resume a publication that stopped with `halted` (3 infrastructure retries used, or an out-of-piece merge diff). L4/L5 can read `payload.halted` / `payload.unknown`; an operator resume (clear `halted`, `infra_retries`, `retry_after`) needs a small endpoint or CLI.
- `STUDIO_PUBLISH_REPO` is honoured only with `STUDIO_REHEARSAL=1`; `live_base` for a rehearsal repo has no Pages, so a rehearsal must keep `STUDIO_LIVE_ENABLED` unset or accept that `live()` cannot confirm.
- Env budgets (seconds): `STUDIO_GATE_BUDGET_S` (3600), `STUDIO_DEPLOY_BUDGET_S` (14400), `STUDIO_LIVE_BUDGET_S` (21600); `STUDIO_PROTECTION_MODE=github|studio` (default github).

## L1 follow-up: studio/server/credentials.py

`GitHubCLI.call` now raises `Infra` (a `Refused` subclass) for a failed GET that is transient (HTTP 5xx/408/429,
gh timeout or missing, network wording). 404 still returns None; 401/403 stay `Refused`. The file is outside the
original L1 ownership; the change is minimal and covered by `CLITransientReads` in `tests/test_studio_publish_robust.py`.
Also: the public ruleset must not be required to carry `strict_required_status_checks_policy`; if it does, Studio
replays the approved bytes on the new main when the PR reports `behind`.

# studio-un-autor

- Actualizar README.md, PUBLICATION_POLICY.md, LOCALIZATION.md y contratos operativos que todavía describen una segunda cuenta obligatoria: el autor selecciona su revisión al pulsar Publicar y pasan todas las compuertas automáticas. No convertir la publicación en una afirmación de revisión humana de idiomas. Fuera del ownership.
- Actualizar tests/harness/mock_github.py y las baterías tests/harness/browser/studio_review.mjs y studio_publish.mjs al contrato de un autor. El adaptador de tests/test_studio_publish.py conserva SHA, protección y checks; sólo retira el requisito de reviews. Reejecutar la batería real en escritorio y pantalla estrecha; conservar sus aserciones de integridad.
- ops/studio/host.py todavía exige ambas cuentas locales para instalar Studio (tests/test_studio_host.py conserva esa prueba). Revisar ese requisito de instalación fuera de este carril; la publicación ya no requiere otra credencial GitHub. No cambiar protección de sesiones.
- Verificar fuera de este entorno la publicación real con la credencial del autor: PR, checks verdes, merge existente, deploy e identidad del artículo público. Si GitHub rechaza el merge por reglas existentes, resolver ese permiso con el operador; este carril no cambia rulesets ni usa otra identidad.
- No hubo inspección final en navegador real: faltan Chromium/Playwright y las dependencias declaradas prosemirror-model/esbuild. No instalar dependencias ni usar red aquí. La batería JS disponible prueba el controlador con DOM simulado y el bundle servido, no su aspecto visual.

# studio-inventos

`docs/lanes/BRIEF-STUDIO-INVENTOS.md` incluye una ruta absoluta del host. El
gate `NO_MACHINE_PATHS` la detecta en el árbol versionado y bloquea
`test_tracked_source_tree_passes_machine_path_gate`, `test_complete_invented_piece_with_company_and_quote_passes`
y dos recorridos integrales de publicación.

Cambio exacto fuera del ownership: reemplazar la ruta absoluta del brief por
una referencia relativa al repositorio, sin cambiar las instrucciones del
carril. Reejecutar `python3 -m unittest discover -s tests -p 'test_studio_*.py'`.

# newswire-bridge-20261027

- ARB: aplicar `.scratch/arb-fix.patch` en su repositorio privado. El compilador
  `tools/build_public_release.py` debe reconstruir `data/corrections.json` con
  `PUBLIC_CORRECTION_FIELDS`, excluyendo `run_id` y futuros campos internos, sin
  borrar eventos ni cambiar su prosa pública. El parche incluye tres pruebas
  sintéticas y las conecta al sello en `tools/validate_publication_plane.py`;
  antes falla la exclusión de metadatos y el rechazo estructural,
  después pasan. El sellado real parcheado y la cuarentena permiten verificar
  730 registros y conservar los 176 eventos de corrección. No modificar el export
  de sólo lectura ni omitir el verificador estricto.
- La causa histórica exacta del `step_exit=128` no se puede recuperar del log:
  stderr privado fue descartado y no existe el checkout Git de ARB. El fallo
  ocurre antes de cualquier resultado real del sello de main. Clonación y fetch
  son candidatos; no hay evidencia que permita atribuirlo a facturación, un SHA
  ausente o checkout. El bridge ahora reintenta ambas operaciones tres veces y
  informa la fase mediante el reportero aislado de códigos cerrados en el resumen
  del job; la salida directa conserva sólo `step_exit` numérico. Ejecutar el
  workflow fuera y conservar ese código si persiste; no abrir logs
  privados ni desactivar linaje, sello o guardas para obtenerlo.
- Humanos: resolver la facturación de Actions de ARB; queda fuera de este carril.
  No se ha desplegado, hecho push, accedido a cuentas ni verificado recuperación
  en producción. Ejecutar las aceptaciones con pytest fuera: este entorno sólo
  dispone de python3/unittest y no permite añadir dependencias.

- Revalidación final: suite completa en ocho shards aislados sobre `origin/main`
  (`d7a1316d0`) y el candidato `1d6cff88d`: 1,283 / 1,292 pruebas descubiertas,
  1,277 / 1,286 reportadas por unittest, cero fallos, las mismas nueve omisiones
  (incluidas dos clases de navegador). Cero fallos u omisiones nuevos.
  Evidencia local en `.scratch/full-suite-results/comparison.json`.
- La primera comparación detectó dos regresiones introducidas por el diagnóstico
  directo de selección. Se corrigieron sin cambiar las guardas originales:
  salida numérica exacta y reportero aislado de códigos cerrados. Las 127 pruebas
  focalizadas del bridge/privacidad/selección y las 19 del parche ARB pasan.
  El export real pasa sólo tras aplicar el parche ARB en una copia y poner en
  cuarentena dos registros: 730 admitidos, 176 correcciones conservadas.

# newsroom-refresh-20261027

- Hallazgo incidental, fuera del arreglo del refresh: durante la suite en
  paralelo, `tests/test_publish_processes.py::running` recibió
  `ProcessLookupError` al leer el estado de un proceso que acababa de terminar.
  El helper sólo captura `FileNotFoundError`. El módulo repitió sus cuatro
  pruebas sin fallos. Para cerrar esa carrera, capturar también
  `ProcessLookupError` en ese helper y devolver `False`, manteniendo todas las
  aserciones de limpieza y terminación; añadir una reproducción determinista
  del ESRCH. No se modificó ese módulo en este carril.
- `test_studio_journey_timing.JourneyTiming.test_probe_measures_real_authenticated_preview_without_credential_receipt`
  falla de la misma manera en base y carril bajo la ejecución concurrente:
  `measure_preview` no recibe el ensayo del renderer. Es un hallazgo compartido,
  no un fallo nuevo. Repetir el recorrido aislado y examinar el diagnóstico del
  renderer antes de modificar presupuestos o atribuir la causa; conservar las
  aserciones de entrega y de ausencia de credenciales.
- `test_studio_translation.TranslationHTTPTests.test_real_authenticated_http_translate_preview_and_distribution`
  también falla en ambas copias concurrentes: timeout HTTP y luego directorio
  no vacío durante la limpieza de la vista previa. Repetir sin carga concurrente
  y verificar que el renderer termina antes de limpiar su directorio temporal;
  no aumentar el timeout ni omitir la distribución como arreglo del refresh.
- Ejecutar el refresh y verificar edición/frescura en producción después de la
  integración. Este carril sólo reconstruye y verifica un candidato local,
  sin red, push, despliegue ni inspección del sitio vivo.

# hero-titular-largo-20261027

UNVERIFIED: falta Playwright en este sandbox. Tanto el intento previo como el
posterior de `tests/oraculos/verificar_paper.py` terminaron con
`BROWSER_UNAVAILABLE`, antes de medir el layout. No se afirma que el titular ya
ocupe cuatro líneas, que móvil esté verificado ni que el Deploy esté reparado.

Continuación fuera del sandbox, con el navegador del workflow disponible:

```sh
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --editorial editorial --out publish --base /FCMO-AI-Newsletter/
python3 tests/oraculos/verificar_paper.py publish
```

Conservar los presupuestos originales: máximo cuatro líneas a 1440 px y altura
del titular no mayor al 45 % de 844 px a 390 px. Revisar visualmente ambas medidas
antes de promover el cambio. La clasificación usa el tamaño `title-large` ya
existente; la prueba sin navegador no demuestra los píxeles finales.

El árbol actual tiene 736 historias (731 live) y abre con la ficha de OpenAI,
distinta de las tres historias capturadas en el brief. Las regresiones conservan
los textos exactos del incidente y el titular mixto CJK/latino actual. No se
modificaron datos, oráculos ni sus presupuestos.

# hero-titular-largo-20261027 — ronda 2

En juego → legibilidad del titular completo dentro del diseño aprobado → evidencia
exigida: Chromium a 1440 y 390 px con los presupuestos originales → evidencia que
hay: regresión de clasificación roja antes/verde después, HTML completo, build y
estimación con las métricas de la fuente real. NO-GO para afirmar layout o Deploy
reparados mientras falte la medición de navegador. No hay publicación en este carril.

## Derivación y límite

- Columna a 1440: `(1360 - 2*56 - 57.6) * 7/12 = 694.4 px`.
  `paper.css` da large = `3.4vw` = 48.96 px, compact = `3.3vw` =
  47.52 px y extra-compact = `min(2.1vw, 1.9rem)` = 30.24 px.
- Estimación offline con FreeType/HarfBuzz, la WOFF2 Inter Tight local a peso 900,
  tracking final -0.020em y word-spacing +0.020em. Entre 1122 títulos EN/ES del
  árbol actual, los primeros casos de cinco líneas por ajuste de palabras son
  ANVIL (42.4 unidades) en large y OSS-Fuzz (46 unidades) en compact.
  Esto calibra, pero no sustituye `text-wrap:balance` ni Chromium.
- Cortes exclusivos del hero: compact >38, extra-compact >45. El primer corte
  deja margen frente a 42.4 y conserva las tres clases largas en los probes c6
  existentes (38.5/39.1 unidades ya prueban compact). No se cambia ningún probe,
  oráculo, presupuesto, texto publicado, CSS ni corte de story header.
- El español exacto de 107 caracteres pasa de large a extra-compact. Los probes
  ES de 107/129/130 caracteres calculan 3 líneas a 1440; a 390, columna 358 px,
  tamaño existente 32 px y tracking -0.012em: 6/7/8 líneas, alturas estimadas
  203.52/237.44/271.36 px, todas bajo 379.8 px. Son cálculos, no mediciones DOM.
- Para Han de avance 1em, extra-compact admite 22 caracteres por línea en
  694.4 px: hasta 88 en cuatro líneas. Los probes de 70 y 80 Han entran en ese
  alcance. **107/130 Han puros no caben**: requieren 5/6 líneas a 1440 y,
  con 32 px y leading 1.3, 10/12 líneas (416/499.2 px) a 390. Para 130 Han
  harían falta <=21.04 px en desktop, fuera de las clases existentes. Se deja
  este límite explícito; no se inventa una escala ni se trunca el texto.

## Continuación ejecutable fuera del sandbox

```sh
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --editorial editorial --out publish --base /FCMO-AI-Newsletter/
python3 tests/check_paper_hero_titles.py publish
python3 tests/oraculos/verificar_paper.py publish
git diff --check
```

UNVERIFIED: los dos comandos de navegador terminan con `BROWSER_UNAVAILABLE`
porque no existe Playwright instalado aquí. La batería nueva mide los ocho
textos completos en sus portadas nativas a 1440/390, sin sockets ni peticiones
externas. Sus controles con fake aceptan mediciones sanas y rechazan cinco
líneas, 380 px móviles, overflow, siguiente línea ausente y pérdida de texto;
no cuentan como evidencia de layout real. Falta revisión visual de Claude.

## CANON aplicado

- `Hub:runtime/FCMO_RUNTIME_V1.txt`: no transformar build/estimación en una afirmación de layout verificado.
- `Hub:AGENTS.md`: cargar software, visual e identidad por la superficie afectada; no abrir una campaña ajena al arreglo.
- `Hub:standard/CORE.md`: L5 cambió la prueba: conservar el oráculo real y añadir una batería de textos exactos; no cerrar la verificación con la clase CSS.
- `Hub:disciplines/SOFTWARE_ENGINEERING.md`: observar tres fallos de regresión antes de modificar producción y conservar los cortes del story header.
- `Hub:disciplines/VISUAL_ENGINEERING.md`: renderizar será condición para afirmar las cuatro líneas; las métricas offline sólo calibran.
- `Hub:identity/README.md`: preservar la jurisdicción propia de FCMO AI y la escala existente del producto.
- `Hub:identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt`: reutilizar Inter Tight y escalones existentes; no inventar un tamaño para hacer caber 130 Han.
- `Hub:identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt`: no cambió nada porque no se tocan marca, símbolos ni geometría del isotipo.
- `Hub:identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md`: no cambió nada porque el arreglo no altera atmósfera ni niveles de exposición técnica.
- `Hub:disciplines/WORTHY_WORK.md`: PROOF separa la batería fake del resultado para el lector; no declarar listo sin navegador.
- `Hub:identity/FCMO_EDITORIAL_SOCIAL_OS_v0.1.md`: no cambió nada porque excluye FCMO AI/product UI y no se produce copy social.
- `Hub:disciplines/COMMUNICATION.md`: informar en español el resultado y su límite, con cifras estimadas identificadas como tales.

El contrato nuevo de cortes de hero cambia NgramRL (42 unidades) de large a
compact. Sus dos aserciones de clase se actualizan por ese cambio de contrato
explícito del brief; siguen exigiendo la clase exacta y el titular íntegro.
Las aserciones de los otros leads y del story header se conservan. Los 2193
HTML con story header son idénticos byte a byte al candidato anterior.

Las referencias `Hub:` son relativas al checkout canónico; su ubicación completa
se informa sólo en el reporte al operador. Las rutas absolutas que añadí aquí
activaban correctamente `NO_MACHINE_PATHS` y hacían fallar privacidad/Studio.
Se retiraron del documento público, sin modificar esa compuerta: sus 7 pruebas
y las 2 integraciones HTTP afectadas pasan tras la corrección. La primera
comparación con el builder base conservaba este documento cambiado y no era
un aislamiento válido para atribuir el fallo a la base.

## Aceptación de la ronda 2

- Build con el comando anterior: salida 0, 5805 rutas, 57 feeds y 3862 redirects.
- `python3 -m unittest discover -s tests -p 'test_paper_hero_titles.py' -v`:
  9/9 verdes. Los dos métodos nuevos de clasificación ejecutados con la función
  original de 690d98efe vuelven a fallar (3 aserciones), incluido el español exacto.
- `python3 -m unittest discover -s tests -p 'test_c6_tablet_oracle.py' -v`:
  22/22 verdes, sin modificar el oráculo ni sus tests.
- `python3 tools/unittest_shards.py --index <0..3> --count 4`: las cuatro
  particiones terminaron, con 1309 pruebas descubiertas, digest común
  `f3682a573232e30682111c98789f725d5ebc5b4483df858b1e52bc244802d074`.
  Unittest reportó 1303 pruebas y 9 skips (las clases saltadas no cuentan sus
  métodos en `testsRun`). Las corridas intermedias NO fueron verdes: detectaron
  las dos expectativas NgramRL y las rutas internas del handoff ya corregidas.
- Repeticiones tras corregir cada causa: hero 9/9, c6 tablet 22/22,
  `tests.test_studio_checks_privacy` 7/7, las dos integraciones HTTP afectadas
  2/2, `tests.test_gates` 25/25 y
  `tests.test_v4_corpus_freshness.CorpusFreshnessBuildTests.test_publication_gates_pass_on_the_fresh_build`
  1/1 con sus dos builds y 14 compuertas por build. Total: 66 comprobaciones
  repetidas verdes; no quedan fallos observados sin corregir. No se afirma una
  nueva corrida completa única en verde después de las correcciones. La corrida
  serial inicial, redundante y con código cargado anterior, fue interrumpida
  después de terminar las cuatro particiones.
- `git diff --check` y `git diff --cached --check`: verdes.
- `tests/check_paper_hero_titles.py publish` y `tests/oraculos/verificar_paper.py publish`:
  salida 1, `BROWSER_UNAVAILABLE`. Los skips existentes de navegador también
  quedan UNVERIFIED. Reejecutar suite y navegador fuera del sandbox.

# nl-deploy3 — regresiones de Deploy 40545640286

En juego → conservar la degradación de evidencia ya admitida y la legibilidad
móvil del diseño existente → evidencia exigida: igualdad de overlays contra
su fuente publicada, regresión de localización y Chromium sobre el candidato
real → evidencia que hay: fallo de localización reproducido antes del cambio,
JSON del oráculo fallido y comprobaciones locales descritas abajo → GO para
revisión del código; NO-GO para afirmar Deploy o layout reparados sin Chromium.
Ética: NO_MATERIAL; este carril no publica, envía mensajes ni cambia prosa editorial.

## Causa y arreglo de localización

- Fallo reproducido en `cb8f8dad7` con
  `python3 -m unittest tests.test_localization_completeness`: 41 tests,
  1 fallo y 1 skip; `FCMO-841949AEA161`, último claim del overlay español.
- El lote recibido en `d263c4f4c` degradó el claim a `CLAIMED`. La release
  `626b73213` ya había importado esa corrección en ES/ZH; su inglés admitido
  y el inglés recibido actual son idénticos para ese registro. El overlay
  publicado coincide íntegramente con el delta actual en ambos idiomas.
- `15425e7ad` había autorizado contrastar el overlay completo con esa fuente,
  pero lo condicionó al digest global. Los lotes posteriores avanzaron el
  corpus, `release_lags_corpus` volvió a verdadero y la prueba exigió otra vez
  `DEMONSTRATED_THIRD_PARTY_EVALUATION_REPORT` del snapshot `c4ad8f2`.
- La prueba decide ahora por igualdad exacta del inglés publicado y recibido
  de cada registro, manteniendo la exclusión de `carried_ids` y la igualdad
  completa del overlay. No cambia el corpus ni restaura evidencia antigua.
  El snapshot histórico permanece intacto. Una prueba adicional altera label
  y prosa en ES/ZH y confirma que las cuatro alteraciones siguen siendo rechazadas.

## Causa y arreglo móvil

- Se extrajo el JSON del fallo y se ejecutó `evaluate` del oráculo existente:
  la única infracción es `tabbar-clear es-419 390x844 front`. `receiptNa`
  termina en `792.4375`; la barra empieza en `780`. El titular empieza en
  `164.6875`, termina en `368.125` y mide `203.4375` de alto. No fallan
  `h1-top`, banner, freshness, overflow ni el resto de idiomas.
- El nuevo titular español de 107 caracteres usa `title-extra-compact`.
  La regla móvil a <=520 daba `1.6rem`/1.05 a `medium`/`large`, pero no a
  `compact`/`extra-compact`: estas heredaban `2rem`/1.06 (32 px).
  Cambiar a una clase compacta agrandaba el titular y empujaba el aviso inferior.
- Se extiende a las cuatro clases latinas la misma regla móvil existente de
  `1.6rem`/1.05, con `:is` de igual especificidad. Se conserva el texto íntegro,
  la tipografía, los márgenes, CJK y las reglas desktop. Reducir el bloque del
  titular deja más altura al aviso; su posición final aún requiere Chromium.
- La batería `tests/check_paper_hero_titles.py` añade una invariante de estilo
  computado: compact/extra-compact no pueden ser mayores que medium a 390 px.
  El fake rechaza también la inversión 32 > 25.6; prueba el evaluador, no los
  píxeles. Se mantienen los presupuestos de cuatro líneas y 45% de altura.
  El rojo anterior del layout está probado por el log de CI; no hay medición
  verde local del layout porque no existe Playwright en este checkout.

## Aceptación local

- `python3 -m unittest tests.test_localization_completeness`: salida 0,
  42 tests, 41 pasan y 1 skip existente por desfase corpus/release.
- `python3 -m unittest tests.test_paper_hero_titles tests.test_v4_mobile_first_viewport tests.test_c6_tablet_oracle tests.test_design_v2 tests.test_c6_design_contract tests.test_story_layer.TaxonomyTests`:
  salida 0, 69 tests, 67 pasan y 2 skips existentes de navegador.
  No se ejecutó de nuevo la suite completa.
- `python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --editorial editorial --out publish --base /FCMO-AI-Newsletter/`:
  salida 0, 5805 rutas, 57 feeds, 3862 redirects, 7202 bytes de JS.
- `python3 design/build_css.py --check`: salida 1 por presupuesto preexistente.
  Reproducción con los bytes de `cb8f8dad7` en un temporal: misma salida 1.
  Base: 115466 bytes; candidato: 115431; límite intacto: 114688.
  El arreglo reduce 35 bytes; el exceso restante es 743 bytes y se deja como
  deuda separada, sin elevar el límite ni minificar reglas ajenas al defecto.
- `python3 tools/gates/run_all.py publish`: salida 0, `GATES PASS (14/14)`;
  conserva los avisos no bloqueantes existentes de glosario y localización.
- Tras el ajuste final de selector y la documentación:
  `python3 -m unittest tests.test_paper_hero_titles tests.test_studio_checks_privacy`:
  salida 0, 16/16 sin skips. `no_machine_paths.check(Path("publish"))`:
  8171 archivos, sin advertencias.
- `git diff --check`: salida 0.

## UNVERIFIED y continuación fuera

Los tres comandos siguientes se intentaron aquí y devolvieron salida 1 con
`BROWSER_UNAVAILABLE`; ejecutarlos con el Playwright/Chromium instalado en el host:

```sh
python3 tests/oraculos/verificar_mobile_first_viewport.py --print-measurements
python3 tests/check_paper_hero_titles.py publish
python3 tests/oraculos/verificar_paper.py publish
```

El primero reconstruye el candidato y comprueba la regla original `tabbar-clear`
en los tres idiomas. Los otros dos usan el candidato generado por el build
anterior. Hace falta confirmar el aviso entero sobre la barra y revisar el
resultado móvil y desktop; este carril no acredita publicación ni salud en vivo.

## CANON: rutas y decisiones

`Hub:` designa el checkout canónico FCMO Agent Hub. Se usan referencias relativas
para respetar la compuerta pública `NO_MACHINE_PATHS`.

- `Hub:runtime/FCMO_RUNTIME_V1.txt`: el build local no se presenta como Deploy ni como layout verificado.
- `Hub:AGENTS.md`: se cargaron software, visual e identidad por el resultado afectado; no se inició trabajo ajeno al carril.
- `Hub:standard/CORE.md`: L2/L5 cambiaron la decisión: usar la versión inglesa admitida por registro y el JSON de medidas; no culpar a h1-top ni modificar el umbral del oráculo.
- `Hub:disciplines/SOFTWARE_ENGINEERING.md`: se reprodujo el rojo de localización antes de editar; se preservó el fallo de CI como evidencia del defecto móvil.
- `Hub:disciplines/VISUAL_ENGINEERING.md`: no ocultar ni truncar el aviso para lograr la primera pantalla; reservar el visto bueno visual para Chromium.
- `Hub:identity/README.md`: mantener el diseño propio de FCMO AI; no importar el diseño de Javier/fCMO ni rediseñar la portada.
- `Hub:identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt`: reutilizar la familia y la jerarquía tipográfica existentes, sin inventar otra escala.
- `Hub:identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt`: no cambió nada porque no se modifican marcas, caret, naranja ni geometría simbólica.
- `Hub:identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md`: no cambió nada porque no se modifica la atmósfera ni la profundidad técnica de ninguna superficie.
- `Hub:disciplines/WORTHY_WORK.md`: PROOF separa el evaluador fake, las pruebas locales y la legibilidad del lector; no dar esta última por probada sin navegador.
- `Hub:identity/FCMO_EDITORIAL_SOCIAL_OS_v0.1.md`: no cambió nada porque excluye la identidad FCMO AI y product UI; tampoco se crea copy social.
- `Hub:disciplines/COMMUNICATION.md`: comunicar en español la causa, el resultado y la frontera no verificada sin presentar trabajo local como publicación.
- `Hub:governance/KNOWLEDGE_FRESHNESS.md`: un digest posterior no invalida una corrección ya admitida; conservar la versión histórica y distinguir el corpus recibido del publicado.
- `Hub:ecosystem/repositories.json`: confirmó la autoridad local de Newsletter pese al preámbulo genérico de Claudex; las pruebas y contratos aplicados son los de este repo.
# nl-d-core

## Límite de entrega

Núcleo D implementado desde registros reales, sin despliegue. No se declara coincidencia 1:1 ni preparación para producción: falta inspección de navegador y juicio visual de Claude contra R4. No hay Playwright ni Chromium instalados accesibles; el ejecutor de captura devuelve `BROWSER_UNAVAILABLE`, salida 2. No se instalaron dependencias ni se usó red.

## Continuación exacta de las capturas

Desde la raíz del worktree, con un Playwright **ya instalado** en el host:

```sh
python3 tools/paper/build.py --stories contracts/fixtures/stories.v2.json --status contracts/fixtures/newsroom-status.fresh.json --editorial tests/fixtures/editorial --out /tmp/nl-d-core-fixture-site --base /paper/
PLAYWRIGHT_MODULE=/ruta/absoluta/al/playwright/index.js python3 tests/test_d_visual.py --site /tmp/nl-d-core-fixture-site --base /paper/ --capture design/d-libro/capturas/core
```

La batería usa intercepción de archivos locales, sin servidor ni acceso externo. Captura EN/ES/中文 a 1440/390/320, cada tipo disponible de página, PNG ≤400 KB (recorte vertical sin reescalar). Comprueba desbordamiento horizontal, encabezado, nav/pie, controles de 44 px, menú móvil, búsqueda y recursos ausentes. Guarda `battery.json`; cualquier fallo devuelve salida 1. Sus pruebas unitarias verifican el plan, **no** que el navegador o el diseño hayan pasado. Comparar cada PNG con R4-portada, R4-historia, R4-archivo, R4-metodo y R4-movil-portada y corregir proporciones sólo después de observarlas.

## Integración fuera de propiedad

- **Plates — integrador / propietario de `tools/paper/plates.py` y activos.** El contrato pide reutilizar `plates.py`, y se cumplió. El proveedor existente genera SVG procedurales abstractos, con acentos naranjas propios; el raster de referencia muestra material fotográfico. La diferencia queda para el juicio visual contra R4: no se fingió equivalencia ni se inventó autorización para nuevos activos. Si ese juicio exige cambiar el proveedor, corresponde al propietario de plates y activos, fuera de este carril.
- **Cartas — nl-d-cartas + integrador.** La portada continúa usando las salidas reales de `essays.render_shelf` y `render_issue_shelf`; no se inventaron tarjetas. La salida Ghost sin edición localizada no entra en la portada. El nuevo índice `/letters/` evita un destino muerto en el nav y utiliza ese mismo contenido publicado, con estado vacío localizado. Integrar `render_letters_shelf(letters, locale_code)` cuando el otro carril concrete módulo y estructura de datos; sustituir sólo la composición de tarjetas/índice, preservando autorización y localización. `tools/paper/redirects.py:LEGACY_FRONT_ROUTES` aún contiene `cartas/`: decidir y corregir ahí si el índice D final será `/cartas/`, para que el escritor final no lo sobrescriba con la redirección heredada. Este archivo y los del otro carril no se tocaron.
- **Relaciones de evidencia — propietario del esquema/datos.** El registro actual contiene listas de afirmaciones y fuentes, sin aristas por afirmación. `.d-claims-sources` presenta ambas listas completas sin inventar atribuciones individuales; el mapa agrupa fuentes, afirmaciones y huecos reales. Un grafo de relaciones 1:1 requiere aristas explícitas verificables en el esquema, ingestión y fixtures. No inferirlas por posición ni conectar cada fuente con cada afirmación como si estuviera demostrado.
- **Oráculos anteriores — integrador de pruebas.** El contrato D exige retirar Source Serif y el layout C6 anterior. No se modificó ni debilitó ninguna prueba existente. `test_paper_build` todavía exige tres precargas tipográficas; D precarga las dos familias autorizadas. Los oráculos C6 que busquen estructura/medidas del diseño sustituido requieren una decisión de contrato y nuevos oráculos D, manteniendo intactos privacidad, localización, atribución y frescura. Se detallarán abajo los resultados exactos.
- **Generador CSS — integrador.** `python3 design/build_css.py --check` falla por `paper.css exceeds 114688 bytes` tanto en `origin/main` como en este carril. Los tokens D sí están sincronizados. No se elevó el límite ni se cambió `paper.css` para ocultarlo.

## Evidencia conservada durante el trabajo

Se observaron rojas antes de corregir: cuatro comprobaciones iniciales de integración D; número duplicado y mapa de una sola columna; pérdida del prefijo en cambio de idioma y enlace Cartas sin destino; ausencia de nodos de afirmación; pérdida de autor/medio/fecha de una fuente. Los tests nuevos conservan las aserciones y pasan después. Logs temporales: `/tmp/nl-d-core-red.log`, `components-red.log`, `nav-red.log`, `map-red.log`, `attribution-red.log` (los últimos cuatro con prefijo `/tmp/nl-d-core-`). El build por CLI con fixtures y tres ediciones produjo 210 rutas, 57 feeds y 210 redirecciones. No se verificó producción porque el brief prohíbe desplegar.

## CANON leído y aplicado

Rutas relativas al checkout canónico de FCMO-Agent-Hub, revisión requerida `63ad43b033265dbb17f1b4653d612a972fdbf357`:

- `standard/CORE.md`: autoridad y evidencia; no despliegue ni afirmación de 1:1 sin navegador.
- `runtime/FCMO_RUNTIME_V1.txt`: limitar cada afirmación a la evidencia; separar generación, inspección y producción.
- `AGENTS.md`: cargar disciplinas pertinentes y buscar decisiones anteriores en la única vault; CLI KB ausente, búsqueda directa de procedencia de traducciones.
- `disciplines/SOFTWARE_ENGINEERING.md`: reproducir antes de corregir y verificar por la entrada CLI real, con fixtures y el corpus comprometido.
- `disciplines/VISUAL_ENGINEERING.md`: referencias R4 como criterio visual; batería de tamaños e idiomas, sin sustituir inspección por tests HTML.
- `identity/README.md`: jerarquía de fuentes canónicas; usar la identidad FCMO AI existente, sin crear otra marca.
- `identity/readable/original/FCMO_Design_Current_V4.0.1_UNCHANGED.txt`: Ink/Bone, dos familias tipográficas, reglas rectas y Mêtis limitado a los acentos autorizados.
- `identity/readable/original/Desglose_de_la_simbologia_de_FCMO_UNCHANGED.txt`: conservar el símbolo existente, sin redibujarlo ni reinterpretarlo ornamentalmente.
- `identity/FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md`: evidencia legible y detalle técnico bajo divulgación progresiva, sin exponer maquinaria interna como contenido editorial.
- `disciplines/WORTHY_WORK.md`: priorizar navegación utilizable, evidencia completa y prueba reproducible sobre adornos sin inspección.
- `disciplines/HIGH_CONSEQUENCE.md`: evidencia proporcional; un build no acredita el resultado público ni autoriza publicación.
- `disciplines/COMMUNICATION.md`: reportar el resultado y su límite concreto, conservando los avisos de automatización y traducción.
- `identity/FCMO_EDITORIAL_SOCIAL_OS_v0.1.md`: no cambió copy editorial porque este carril sólo compone la interfaz con registros/catálogos existentes; no creó promesas comerciales ni publicaciones sociales.

Revalidación local: al cierre de la inspección del Hub, HEAD era `1eb9b9f2486875d73c3ab7494a5c72900c3a8074`, posterior al `63ad43b` del brief. La comparación de los trece documentos requeridos sólo encontró añadidos en VISUAL_ENGINEERING e identity/README; se leyeron. Se cargaron también `governance/KNOWLEDGE_FRESHNESS.md`, el índice selectivo `commons/knowledge_registry.json`, `identity/galeria/README.md` y las fichas de Newsletter D R4 e imágenes c6. Confirmaron la necesidad de comparar contra R4 y la diferencia entre fotografía material D y plates abstractas c6; no justifican declarar acabado el diseño sin capturas.

## Verificación adicional de integración

- Comprobación estática del build de fixtures: 210 rutas, 10 575 destinos locales de enlaces/recursos comprobados, 0 ausentes.
- `python3 tools/gates/run_all.py /tmp/nl-d-core-fixture-site`: con el prefijo de prueba `/paper/`, la compuerta de referencias asume el montaje canónico y rechaza los iconos. La comprobación directa de destinos anterior sí los encuentra. No se cambió la compuerta.
- Se reconstruyó con `--base /FCMO-AI-Newsletter/` en `/tmp/nl-d-core-gate-site`: las primeras diez compuertas pasan; `NO_MACHINE_PATHS` bloquea el conjunto por rutas del servidor en los dos `design/d-libro/BRIEF-nl-d-*.md` preexistentes. Esos briefs están fuera de propiedad; el integrador debe sustituir esas rutas por referencias relativas o trasladar esas instrucciones fuera del árbol público, sin crear una excepción al gate. La sección añadida aquí no contiene esas rutas prohibidas. `AGENT_LAYER`, `NO_FCMO_GROUP` y `PIECE_VALID` se ejecutaron individualmente y pasan; el conjunto global **no** se reporta aprobado.
- La ejecución inicial de las 65 pruebas C6 encontró cuatro fallos y un error por retirar la celda de apertura. Se conservó su comportamiento de lectura dentro de la columna D: el cuerpo continúa tras la bajada en escritorio y conserva la apertura en móvil. Dos nuevas pruebas reprodujeron la ausencia del componente antes de corregirlo. Se mantiene íntegro el texto restante, incluso cuando la bajada se corta por presupuesto. Se amplió también la batería del navegador a todos los enlaces visibles del nav/pie; la altura real de 44 px sigue pendiente de navegador.

## Aceptación final del carril

| Comando / comprobación | Resultado observado |
| --- | --- |
| `python3 -m unittest discover -s tests -p 'test_d_*.py'` | 26 pruebas, OK (22,266 s; después de las correcciones de contenido). Build del corpus comprometido: 5 622 rutas, 57 feeds y 3 731 redirecciones. |
| `python3 -m unittest discover -s tests -p 'test_c6_*.py'` | Resumen literal: `Ran 65 tests`, `OK (skipped=4)`; omisiones por navegador no disponible, incluida una clase completa; 0 fallos/errores. Las pruebas de DOM sin navegador no acreditan las métricas visuales omitidas. |
| `python3 -m unittest discover -s tests -p test_paper_build.py` | 31 pruebas: 30 pasan, 1 falla por exigir tres precargas frente a las dos familias D. Prueba existente intacta, decisión de contrato pendiente del integrador. |
| `python3 -m unittest discover -s tests -p test_paper_listing_pagination.py` | 3 pruebas, OK. |
| `python3 design/check_contrast.py` | OK, 24 parejas. Además la prueba D verifica Bone/Fog/Stone sobre Ink e Ink/Body sobre Bone, todas AA. |
| `python3 design/build_css.py --check` | Fallo preexistente en `origin/main` y candidato: tamaño de `paper.css` supera 114 688 bytes; tokens D sincronizados. |
| `python3 tests/test_d_visual.py --site /tmp/nl-d-core-fixture-site --base /paper/ --capture design/d-libro/capturas/core` | Salida 2, `BROWSER_UNAVAILABLE`; 0 capturas. Comando de continuación arriba. |
| JavaScript de filtros de producción ejecutado con Node y DOM controlado | 6/6: estado sin filtros, clase de evidencia, tema + organización, OR dentro de un grupo, cero resultados, restablecer; agrupaciones vacías y contador coherentes. No es prueba de navegador. |
| `git diff --check` y revisión de propiedad | OK; sólo archivos autorizados y esta sección añadida de `NEEDS.md`. |

Base completa observada: `Ran 1270 tests in 2133.167s`, `OK (skipped=9)`. Primer candidato completo: `Ran 1294 tests in 2160.548s`, `FAILED (failures=29, errors=30, skipped=9)`. Esos rojos motivaron las correcciones siguientes; la aceptación completa del candidato final se agrega abajo al terminar. Base real: `origin/main` = `81536f52da12e7816dc1b0e85a75d46efb1ad74e`; inicio del carril = `6bfa4524e445b610ccb0f18e00cb70b71cf14977`. La base se ejecuta en un worktree propio con metadatos git reales, sin red. Las ejecuciones intermedias canceladas no se presentan como suites completas.

Corrección intermedia: `aa83132c2` conserva el cero numérico en el escape HTML. Se amplió la prueba de estadísticas existente a 0/12, se observó el fallo del cero y se corrigió; las 23 pruebas D vuelven a pasar (31,372 s). Después se añadió `43f2baf36`: una corrección sin traducción muestra el aviso localizado de traducción pendiente, no una falsa ausencia de correcciones. El corpus actual tiene cinco correcciones completas; la nueva prueba reproduce la variante faltante antes del cambio. Ese log acredita el primer candidato completo, anterior a `9a3fc6597` y `1ee9f7c5c`; no acredita el código final. El resultado final fragmentado y sus límites se detallan abajo. La batería D final independiente pasó las 24 pruebas en 19,870 s (`/tmp/nl-d-core-d-acceptance.log`).

Cambio exacto solicitado al integrador para tipografía: en `tests/test_paper_build.py`, `test_fonts_are_woff2_subsetted_and_first_paint_preloads_only_latin`, actualizar la expectativa de tres precargas a las dos familias que autoriza CONTRATO.md, comprobando explícitamente Inter Tight y JetBrains Mono y ausencia de Source Serif en las precargas. Conservar las comprobaciones de WOFF2, archivos locales y subconjuntos. Este carril no puede modificar ese test existente y no añadió una precarga innecesaria para satisfacer el conteo antiguo.


## Correcciones surgidas de la comparación completa

- `9a3fc6597`: vuelve el agregado real del corpus a la leyenda D (historias/temas/organizaciones y las tres clases, sin ascender evidencia ausente); no se añade un segundo panel C6. Se conservan los identificadores semánticos de portada, cuerpo y navegación que usan los lectores. Fecha, fuentes, correcciones y sumario nativo completo siguen trazables al registro; `NewsArticle.articleBody` exporta el resumen completo sólo cuando la edición está completa. Se retira del frente el fallback de Ghost sin localización. La nota de traducción pendiente sobre Bone usa Body, AA 9,93:1, frente al Fog/Bone incorrecto 1,28:1 anterior.
- Se observaron rojos en la suite completa antes de esas correcciones. Una nueva prueba del agregado también se ejecutó contra `d_components.py` de `43f2baf36` y falló, antes de pasar con el componente corregido. Las dos pruebas nuevas elevan D a 26. Las pruebas existentes no se modificaron.
- `1ee9f7c5c`: la batería pendiente de navegador comprueba ambas dimensiones de 44 px, incluyendo fechas del calendario y etiquetas de filtro. Se corrige el caso geométrico de siete fechas a 320 px (288 px interiores menos separaciones no permiten siete blancos de 44 px): sin gutters a ese ancho, la retícula cabe en 320 px. Nav móvil, pie y feeds tienen también mínimo horizontal. Esto no sustituye la comprobación física del navegador.
- Los tres fallos de Studio de la primera suite completa se rastrearon a `NO_MACHINE_PATHS`, con los dos briefs identificados en el resultado de privacidad. No se relajó la compuerta, el chequeo de aprobación ni el de publicación simulada.
- Suite final, código congelado en `1ee9f7c5c`: `python3 -m unittest discover -s tests -v`, log temporal `nl-d-core-final-suite.log`. La base ya terminó; las ejecuciones canceladas anteriores no cuentan.

Verificación estática final del build de fixtures en `1ee9f7c5c`: 11 481 destinos locales, 0 ausentes; las cinco filas D coinciden con `front_order` en EN/ES/中文. `node --check` acepta el programa real de la batería de navegador. Su ejecución vuelve a terminar con salida 2 por `BROWSER_UNAVAILABLE`, sin capturas. Las pruebas unitarias del plan de capturas pasan 2/2; no acreditan el navegador.


## Matriz completa de capturas y oráculos D pendientes

El fixture pequeño no tiene una página Temas: su matriz honesta es 99 casos. Para los 108 casos, incluidos 9 de Temas, usar el corpus público comprometido; esta construcción ya pasó en el carril (5 622 rutas, 57 feeds, 3 731 redirecciones).

```sh
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --editorial tests/fixtures/editorial --out /tmp/nl-d-core-corpus-site --base /paper/
PLAYWRIGHT_MODULE=/ruta/absoluta/al/playwright/index.js python3 tests/test_d_visual.py --site /tmp/nl-d-core-corpus-site --base /paper/ --capture design/d-libro/capturas/core
```

No se pidió ni usó red. El ejecutor bloquea recursos externos. Las capturas todavía no existen.

Los oráculos C6 existentes que requieren migración de contrato, por el propietario de pruebas, son:
- `test_v4_front_freshness` / `test_v4_front_plan`: localizar `.d-rank` y sus `li[data-story-id]`; contrastar sus cinco filas con `front_order[:5]`, el héroe con `front_order[0]`, el wire con los siguientes treinta y su ausencia de duplicados respecto a las cinco filas. D repite el titular principal como fila 01, como exige R4; no convertir esa presentación en dos historias distintas ni relajar orden/frescura/idiomas/rutas. El selector C6 de cuatro `plate-card` sobre Bone ya no describe la tabla D sobre Ink.
- `test_v4_mobile_first_viewport`: el contrato D tiene Today/Letters/Topics/Archive/Method/Search, menú nativo en móvil y Correcciones en el pie. Comprobar esos destinos, idiomas, un encabezado y menú utilizable; no exigir la barra inferior C6 retirada por el diseño aprobado.
- `test_paper_build` tipografía: se detalla arriba el reemplazo autorizado por las dos familias D, sin quitar las comprobaciones de archivos/subconjuntos ni cambiar el presupuesto de página.

Los documentos de brief con rutas del servidor deben sanearse fuera de este carril; los gates y sus pruebas permanecen íntegros. La aceptación «sin fallos nuevos frente a origin/main» no se declarará cumplida mientras esos errores y la migración de oráculos sigan abiertos.

Comprobación de propiedad: los 445 renglones originales de `NEEDS.md` siguen como prefijo exacto del archivo; sólo se añadió esta sección. No se modificó ninguna prueba existente ni archivos del carril de cartas.


## Resultado final y entrega — código `1ee9f7c5c`

**No se cumplió la aceptación sin fallos nuevos ni se verificó el 1:1.** Todo el código y las pruebas nuevas están dentro de la propiedad del carril; los pendientes tienen propietario y cambio concreto en las secciones anteriores.

| Verificación | Resultado final |
| --- | --- |
| Base `origin/main` (`81536f52da12e7816dc1b0e85a75d46efb1ad74e`), `python3 -m unittest discover -s tests -v` | `Ran 1270`, `OK (skipped=9)`; 2 133,167 s. |
| Candidato final, mismo comando | Terminó con señal 15 / salida 143, sin resumen. Causa de la señal no identificada. No se reporta como suite completada. |
| Verificación final en dos tramos | **1 296 métodos contabilizados; 7 fallos, 17 errores, 9 omisiones.** Prefijo observado: 1 126 métodos completos, 4 fallos/7 errores/7 omisiones; continuación: `Ran 170 tests in 877.448s`, 3 fallos/10 errores/2 omisiones. |
| Pruebas D | 26, OK; ninguna omitida. |
| Contraste | 24 parejas, OK; además 5 parejas del vocabulario D verificadas por las pruebas. |
| Build de fixtures / corpus | 210 / 5 622 rutas; 57 feeds en ambos, 210 / 3 731 redirecciones. |
| Destinos locales del fixture | 11 481 comprobados, 0 ausentes; orden de cinco filas correcto en los tres idiomas. |
| `git diff --check` / propiedad | OK; 19 archivos autorizados, incluido el añadido de este reporte. |
| Capturas | Salida 2, `BROWSER_UNAVAILABLE`; 0 PNG. Matriz preparada: 108 casos con el corpus completo. |

La continuación se derivó del descubrimiento completo de `unittest`: se descontó cada identificador completado del log, se excluyeron únicamente las dos clases con `setUpClass` omitido ya registrado, y quedaron exactamente 170 identificadores. Se descartó la última prueba iniciada, que había quedado incompleta, y se ejecutó de nuevo en la continuación. La clase de frescura recreó sus fixtures temporales; las dos pruebas previas de esa clase sólo leen resultados. No se cambiaron archivos de código o pruebas entre tramos. El inventario y los resultados temporales se guardan como `nl-d-core-interrupted-manifest.json`, `nl-d-core-tail-result.json` y `nl-d-core-final-results.json`; logs `nl-d-core-final-suite.log` y `nl-d-core-tail.log`. Esta cobertura fragmentada **no** se presenta como éxito del comando único.

Clasificación final de las incidencias (son resultados de pruebas/subpruebas, no un conteo de problemas independientes):
- **Privacidad de los dos briefs:** 11 errores de compuertas y 3 fallos de Studio. `no_machine_paths.check()` se reprodujo directamente en el código final: sólo señala `design/d-libro/BRIEF-nl-d-core.md` y `design/d-libro/BRIEF-nl-d-cartas.md`. Integrador: sustituir el prefijo absoluto del Hub en ambos briefs por un alias relativo `FCMO-Agent-Hub/`, explicado al principio como el checkout canónico externo; conservar el resto del contrato. No exceptuar los briefs de la compuerta.
- **Oráculos C6 frente al contrato D:** 6 errores por selectores de la tabla vieja, 3 fallos de navegación móvil por exigir Correcciones y tabs inferiores en lugar de Cartas/menú D, 1 fallo de tres precargas. Los cambios exactos de contrato están arriba; este carril no puede editar esos tests existentes.
- **Omisiones:** ocho entradas por navegador no disponible (incluyen clases completas) y una condicional de renderer ausente porque el renderer sí está integrado. La comparación de preview/build byte por byte pasó. Los tres oráculos reales de refresco diario también pasaron en copia temporal: crecimiento del generador, historia nueva publicada y ediciones nativas completas.

**UNVERIFIED:** ejecución completa en un solo proceso en el código final; medidas DOM, controles físicos, tipografía CJK y comparación R4 en 1440/390/320; las 108 capturas; juicio visual de Claude y producción. No hubo despliegue. El límite de tamaño del generador CSS antiguo y la integración de Cartas quedan como se describió arriba.

**COMMITS de código** (todos con el coautor requerido):
- `51c664326` Add the D evidence grammar and data-driven components
- `6cf91da22` Render the publication core with the D evidence layout
- `d29679e82` Preserve opening facts across D story breakpoints
- `aa83132c2` Keep known zero counts visible in D evidence statistics
- `43f2baf36` Keep untranslated corrections visible as pending
- `9a3fc6597` Preserve publication facts across the D core
- `1ee9f7c5c` Check both dimensions of mobile control targets
# nl-d-cartas

- `tools/paper/build.py`, page-route generation in `PaperBuilder.build` (the loop that currently writes the `cartas/` redirect): replace the redirect with a data-backed letters index in EN, ES and ZH from published Ghost cartas plus published editorial pieces. Use `community.render_letters_shelf` for the home-page section; generate the reference-matched index markup from the same letter records. The current redirect prevents `/cartas/` from meeting this lane's first-class index requirement, and this file is outside the lane's ownership.
- `tools/paper/build.py`, stylesheet assembly for front-page output: include `assets/css/d/d-letters.css` on the home page so the exported `community.render_letters_shelf` markup receives its owned styles.
- `design/d-libro/BRIEF-nl-d-cartas.md` and `design/d-libro/BRIEF-nl-d-core.md` (outside this lane's ownership): replace private absolute filesystem references with repository-relative paths. The full suite's `NO_MACHINE_PATHS` gate flags both briefs; the same finding cascades into Studio preview tests returning 409. Keep the gate enabled.
