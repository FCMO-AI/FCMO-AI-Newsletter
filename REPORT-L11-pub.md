# L11-pub — protected publishing

Date: 2026-10-04. Branch: `c5/pub`. Base: `a6275de` (v4 reader/design). This is a local implementation report, not a claim of remote enforcement or production publication. No push, merge, remote API, credential change or scheduled-task change was performed.

## Delivered

- Proposed main ruleset in `ops/publish-ruleset.json`: required GitHub Actions `publish-gate`, current main, one independent CODEOWNERS approval, stale approvals dismissed, conversations resolved, no force-push/deletion and no bypass. `ops/publish_ruleset.py` only prints the request and operator command; it has no apply mode.
- `.github/CODEOWNERS` and a read-only required-check workflow on every main PR, without path filtering or secrets. It runs the full suite and immutable candidate validation. Pages retains its own gates and now runs the suite and the historical six-gate boundary. Manual deploy/rollback is restricted to main, and a dispatch from another branch cannot cancel an active main run.
- `ops/publish.py`: a single publish or rollback command dispatches the existing reviewed-main Pages action. Local check/dry-run freezes one source commit, validates in an isolated clone, preserves six legacy gates and all 13 paper gates, requires OG rendering plus the browser oracle, and produces an identity receipt only after success. Ghost variables are discarded for local checks. Missing browser support remains a failure.
- `ops/publish_ledger.py`: plan-first, local-bare-only migration. Creates an orphan ops-ledger tree containing only the ledger, preserving exact bytes, UTC chronology and unique run IDs. Refuses divergent existing state and concurrent creation, and is idempotent for matching state. No push operation. Product branch stops tracking the ledger; historical bytes remain in git.
- Short Spanish operator guide `docs/PUBLISHING.md`, installation and desk-prompt migration guide `docs/PUBLISHING-SETUP.md`.

## Red-first and repairs

`7138874` committed the tests before implementation. The red run failed because the protected-publication module did not exist. `c2e1f65` implemented the path. The first real bare-clone dry-run additionally found inherited receipt drift: READY_TO_PUBLISH measured the previous design tree. `b8eca86` regenerated only its candidate digest through the existing tool, keeping the integrity comparison intact. `4dac3a5` moved the pre-existing ledger chronology test to the real migration boundary and made the production migration enforce that chronology itself.

The ledger relocation initially caused the existing product-file chronology test to fail; it was corrected by preserving the invariant at the new boundary, adding rejection of timezone-free timestamps and duplicates, and checking the ledger cannot remain tracked on the product branch. The complete 58-record historical ledger was checked with that production validator.

## Verified local evidence

- Baseline: 561 tests, zero failures/errors, two pre-existing browser skips.
- Targeted protection/migration checks: 14 tests PASS, including the actual REMOTE_SCRIPT gate rejecting an unsafe synthetic edition before browser/identity stages.
- Six release gates PASS after receipt reconciliation. Current paper build: 459 routes; all 13 gates PASS, including NO_FCMO_GROUP. Existing glossary warnings were retained.
- Full-history migration rehearsal from `7138874a773cc1088c0a15b82f9ea46210c0781f`: 58 records, byte-for-byte equality, SHA-256 `09bc5d189eaba32f1714d743972c9103d8dc11359e86a82365f83bcb8032f820`. Only `refs/heads/ops-ledger` was added in the local bare fixture. Its orphan tree has one file. No existing reference moved.
- Real bare-clone dry-run at `b8eca86`: six gates PASS, 13 gates PASS, then exit 1 because Playwright/Chromium is unavailable. All bare references unchanged, no PASS receipt written.
- Separate bad bare clone: an injected invalid public brand in a source document passes the unchanged six legacy gates but is rejected by the real NO_FCMO_GROUP gate. Exit 1, all refs unchanged, no PASS receipt. The bad source remained confined to the ignored local fixture.
- Compilation and diff whitespace checks PASS. Logs and local fixtures are under ignored `_audit/l11/`; they are evidence aids, not part of the publication.

Final complete suite on an isolated clone of `4dac3a5`: **574 tests in 313.655s, zero failures/errors, two existing browser skips**. The skips are not browser success; the publish path itself still blocks without browser support. Workflow YAML parsing also passed.

## Host continuation and remaining boundaries

1. Re-run `python3 -m unittest discover -s tests`, `python3 tools/verify_release.py`, and build plus `python3 tools/gates/run_all.py CANDIDATE`. The architect must independently repeat the real browser path with installed Playwright 1.63.0 and Chromium:

   ```sh
   git clone --bare --no-hardlinks . ensayo.git
   python3 ops/publish.py --dry-run --local-bare ensayo.git --ref HEAD --receipt ensayo-receipt.json
   ```

   This local environment cannot prove a successful full browser dry-run. No bypass or skip flag was added to publication checks.
2. Before merging ledger deletion, pause the desk, capture the newest source commit with the ledger, seed and remotely verify ops-ledger, update the desk prompt (E4) and the L0/L7 readers, then rotate the desk identity. Merging removal before remote seeding would strand consumers; do not do it in that order.
3. Confirm the actual write-enabled CODEOWNERS identities. Only `@javo-27` is evidenced locally. Add Matías's verified identity or the actual publisher team so Javier's own PR can get independent owner approval.
4. Resolve direct-main writers before activating the ruleset. Both bridge and refresh currently push directly to main; requiring a human owner review for every main change blocks those writers. Their promotion must use an approved PR architecture or another operator-approved compatible design. No bot bypass was introduced. This is a real conflict with unattended ingestion, not solved by this lane's scripts.
5. An administrator must inspect/apply the proposed ruleset, confirm its effective API state and the Actions integration identity, restrict the github-pages environment to main, and prove rejection of desk direct push and unapproved/failed-check PRs. Moving a file does not revoke token rights: main denial depends on the active ruleset, absent bypass, and a desk credential without administration/review/workflow/dispatch permissions.
6. Pages production deployment, LKG recovery, the cold phone publishing exercise, and actual token-denial behavior were not attempted or proved. The brief's local implementation is prepared; remote security and reader-visible production acceptance remain open.

This lane implements the narrower supplied brief (ruleset proposal, ledger isolation, gated publish entry). It does not claim the strategy row's editorial issue form, letter schema, PR preview, 48-hour merge exception or timed phone acceptance. The existing recovery workflow was preserved, not represented as a completed production rollback drill.

## Resumen en español

La publicación protegida está preparada y comprobada hasta las compuertas locales: seis históricas y 13 del periódico. El ledger se migra sin perder registros y una fuente inválida queda bloqueada. Falta comprobar el navegador en el host y activar/verificar la protección remota; antes hay que resolver los pushes automáticos a main y completar los propietarios del código. No se hizo push ni publicación.
