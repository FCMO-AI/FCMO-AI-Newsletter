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
