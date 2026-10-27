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
