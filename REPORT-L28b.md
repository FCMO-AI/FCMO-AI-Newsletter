# L28b — Javier's published pieces through the email dispatcher

Implemented locally on `c5/email-kit`: multilingual piece rendering, provider
dispatch after verified Pages, review gating, lifetime idempotency and a public
content-free record for Studio. No push, real provider call, GitHub state write,
production deploy or recipient email was performed. `studio/` was not edited.

## Implementation

`tools/email_render.py` exposes `render_piece_email`; the new closed-document
renderer covers EN, es-419 and zh-Hans for letters, essays and notes, with the
actual author byline and locale web link. It preserves all essay block/inline
types, source citations, original-language quotations, evidence limitations and
credited figures. Footnotes become numbered, linked endnotes in first-reference
order. HTML/editorial templates are escaped and the forbidden brand is rejected.
The table, colors and type follow the daily email. The historical letter preview
is a data-only wrapper; its obsolete `ghost_url` alias needs no Ghost service.

`PieceEdition` shares `validate_locale`/`render` with daily editions, so Kit and
Brevo reuse their existing creation, destination, fsync intent and reconciliation
code. Production keys are `fcmo-piece:<id>:<locale>`. Kit keeps tag-only filters
and sync-before-broadcast; no form filter or Rules were introduced. Listmonk
supports pieces over its private API with the L26 DOI lists/template; its public
gateway capability remains daily-only. Configuration and its private-runner
boundary are documented in [EMAIL-PROVIDERS.md](docs/EMAIL-PROVIDERS.md).

`dispatch-pieces.yml` uses the same concurrency group as daily email. It discovers
only requested, already published LKG pieces; omitted `distribution.email` means
false. Each locale needs a ready document and strict boolean human review in
`provenance.json`. Unreviewed/pending locales get a reason and no broadcast.
Later review enables only the missing locale. Master-off returns before input
reads or provider construction. Kit seed mode keeps the L27 audience-isolation
check, uses `fcmo-piece-test` keys, and never syncs public forms into seed tags.

Live collection compares public metadata, documents and figure bytes against
the immutable LKG source commit, proves reviewed web pages exist, and rereads
deployment identity. The whole collection is repeated immediately before sends.
A mismatch, missing page, identity change or unknown provider effect fails
closed. Pieces do not inherit the daily newsletter's three-story/time cutoff.

## Public record and recovery

The dedicated branch `email-dispatch-state`, file `dispatch.json`, is the
production hook for Studio. Each record has exactly `piece_id`, `locale`,
`state`, `broadcast_id`, `timestamp`. The file also retains provider identity
and content-free lifetime intent keys. Seed results use `dispatch-test.json`.
No titles, article bodies, subscriber data or credentials enter this record.

`QUEUED` with a confirmed broadcast ID is the hook for «Enviado por correo ✓»;
its detail means scheduled/queued, not delivered. Complete-piece success needs
all three locales. Other states are PENDING, SKIPPED_UNREVIEWED,
SKIPPED_NOT_READY and BLOCKED_RECONCILE. The exact Contents API read path and
example JSON are documented in EMAIL-PROVIDERS.md. No state branch exists as a
result of this local session; the workflow creates it when deployed/authorized.

The workflow persists and reads back lifetime reservations before uploading the
L27 intent artifact and before any broadcast. Contents API writes use the file
SHA precondition. It records each piece's observed result before continuing.
Expired artifacts do not erase lifetime reservations. A lost create response
reconciles an existing scheduled campaign; absence after an earlier reservation
blocks recreation. An uncertain draft is not restarted. Reservations made before
a workflow/upload failure require reconciliation even if no POST happened.
Do not delete intents, rename markers or switch providers to force a retry.
Provider changes require explicit reconciliation/migration of lifetime state.

## Verification

Red-first commit: `afbfe1d`. The initial 12-test run failed with 22 subtest/errors
for missing rendering/dispatch/intent functions and workflow. Normalized evidence
is in [red-first.txt](reports/email-kit/l28b/red-first.txt).

The final focused email suite is **98 tests, OK**. It covers three-locale/kind
rendering, numbered notes and links, strict human review, missing distribution,
master-off, future/draft exclusion, tag filtering and inherited form-filter 422,
seed isolation, no duplicate broadcasts, lost acknowledgements, uncertain drafts,
all four adapters, lifetime restoration, SHA conflicts, public record projection,
live byte/page/identity mismatches, and the actual claim→send→claim→send CLI path.
The second CLI send produced zero new broadcasts.

The final full suite passed **690 tests, OK, 3 existing skips** in 285.376 s,
including the added CLI regression. Evidence is in
[full-tests.txt](reports/email-kit/l28b/full-tests.txt).

Kit, Brevo and retained L26 Listmonk candidates each pass **13/13 publication
gates** and agent hygiene. Retained release verification passes **7/7**.
Python compilation, workflow YAML parsing and `git diff --check` pass. Preview
HTML/text for all three locales is in
[preview](reports/email-kit/l28b/preview/en.html); parsed final structure checks
confirmed unique note IDs, working note/back-reference anchors and source links.

Browser oracle: **BROWSER_UNAVAILABLE**, matching the L27 environment boundary.
No Playwright/browser package was downloaded. No visual approval, native
Listmonk/Postgres re-proof, real provider API compatibility, delivery/MIME or
repeated autonomous production operation is asserted by these fixtures.

## Continuation

Integrate the Studio piece contracts/build and L28a distribution/review changes
before testing real pieces: this worktree currently has no editorial piece tree
or Studio build. It deliberately does not invent unpublished inputs. The fixture
matches the frozen Studio document format and separate provenance file.

Claude must rerun the full suite and gates before integration, inspect the email
previews in a real browser at 390/1440, then prove a reviewed three-language piece
on verified Pages with private Kit seed tags. Repeat the same piece and prove
zero new broadcasts and matching public IDs. Check actual unsubscribe/MIME and
several unattended cycles before enabling a reader audience. Keep lifetime
intents during rollback; master-off stops new scheduling and cannot recall mail.

Reproduce locally without provider credentials:

```sh
python3 -m unittest discover -s tests -p 'test_email*py'
python3 -m unittest discover -s tests
python3 tools/verify_release.py
```

Candidate build/gate commands are the L27 reproduction commands, with the same
public Kit/Brevo configuration and the retained L26 Listmonk public URL. The
new tests use loopback provider fixtures and an injected Contents API only.

## Resumen en español

Las cartas, ensayos y notas de Javier ya tienen renderer EN/ES/ZH y dispatcher
independiente del proveedor. Kit conserva tags; cada idioma requiere revisión
humana. Los intents permanentes evitan duplicados incluso después de caducar
artefactos, y Studio tiene un contrato público exacto para mostrar el estado.
Las pruebas de correo y los gates pasan. Falta integrar Studio, revisar el
resultado en navegador y demostrar envío real y continuidad en producción.
No se hizo push ni se envió correo real.
