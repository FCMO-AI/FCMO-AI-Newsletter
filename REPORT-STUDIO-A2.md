# Studio A2 — server implementation and independent replay

2026-10-04 UTC · branch `c5/studio-a2` · verified software commit `1ddaf23`.
Product base `a6275de`; the previous missing-specification report at `f0223ab`
is superseded. The local binding specification was read completely and remains
untracked, as requested.

## Outcome and acceptance boundary

A2's private server, storage, authentication, publication driver and host-ops
artifacts are implemented and committed. Publication was exercised against a
loopback GitHub/Pages mock, with real local git candidate trees. No push to an
external remote, live publication, service installation, credential-file access,
or mutation of another lane was performed.

**Mandatory preview byte identity is not yet satisfied.** A1's editorial
renderer/contracts and B's essay template/static bundle are absent from this
base. The adapter invokes the production builder with `--editorial`; it fails
closed when that integration is unavailable. The HTTP byte-identity test is
wired to compare against a separate full build, but explicitly skips here.
This report does not claim M1, M2, visual acceptance, human acceptance, or a
running production newspaper.

## Changes

- Python stdlib HTTP server, loopback-only bind, two named accounts, scrypt
  passwords, 30-day Secure/HttpOnly/Strict sessions, per-user lockout, CSRF and
  Origin checks, restrictive CSP, and Spanish/English errors/progress.
- SQLite WAL journal owns acknowledged document bytes and revisions. Atomic
  fsync/rename mirrors are reconstructed from it on startup. Saves preserve
  cursors, reject stale revisions, respect locale locks, and invalidate stale
  language review. Block provenance and source hashes remain private metadata.
- Real `draft/*` worktrees and person-authored checkpoint commits, idle/release/
  named checkpoints, word-level differences, paragraph comments, and restoration
  that checkpoints current work first. A process lock prevents duplicate servers.
- Closed document/source/figure validation, safe links, WebP container/chunk/
  dimension checks, and plain-language publication checks with destinations.
  Document validation implements the closed structure in specification §5.1;
  agreement with A1's actual schema file must be checked after integration.
- Private review before any public effect; only the selected piece or issue is
  copied into a candidate from freshly fetched public main. Unknown files and
  symlinks are rejected. The real candidate command is
  `python3 ops/publish.py --check`; it has no alternative success path.
- Durable effect intent, GitHub reconciliation, author-owned PR and merge,
  separate-person review, required-check/protection verification, pinned merge,
  merge-specific Pages observation and three-locale live article-ID verification.
  Red/refused checks do not merge; ambiguous effects do not blindly repeat.
  Visibility failures remain `deployed_unverified`, with bounded retry timing.
- Curated issues with read-only brief references and language-readiness checks;
  corrections and withdrawal notes use the same review pipeline. Withdrawal
  reasons use the existing tombstone vocabulary. Emergency rollback is a
  confirmed-phrase dispatch request, not a claim of completed restoration.
- Optional private assistant jobs and explicit suggestion acceptance preserve
  machine provenance. Subsequent editing does not fabricate human review.
  Missing workers do not interfere with writing/publication. Deterministic
  layout QA reports unavailable until the integrated editor/browser exists;
  no visual result is invented.
- Private git bundle + SQLite online backup + immutable figures, hashed manifest,
  48 snapshots plus 30 daily retention, integrity-checked restore, relocated
  pending candidate worktrees, and an authenticated HTTP recovery drill.
  Host artifacts are staged under `studio/host-ops` for architect installation.

The authentication bootstrap exceptions are the login endpoint and static login
chrome. They expose no draft data. Private APIs, preview HTML and publication
assets require a per-person session. B's compiled bundle is served read-only;
no substitute UI was produced.

## Red-first evidence

1. `e525dc5`: initial storage/closed-document tests committed before implementation;
   execution failed with `ModuleNotFoundError: studio`.
2. `419255b`: implementation and adversarial mock/storage/auth/backup tests.
3. `5b78665`: bilingual failures/progress and metadata-sensitive preview cache.
4. `3d9d68e`: a second committed red test proved that a curated edition wrongly
   accepted a brief whose selected publication language was pending.
5. `1ddaf23`: reuses the newspaper's `is_complete` rule for that brief and makes
   the final review-state transition atomic. The regression passes.

The first full-suite attempt found a forbidden host path in the superseded
report and recursive temporary placement in an existing refresh oracle. The
report was replaced; the suite was replayed in a disposable local clone with
its temporary directory outside that clone but inside this worktree. No gate,
unrelated oracle, or source tree from another lane was changed to obtain green.

## Verification actually executed

- Full suite on a local clone of **`1ddaf23`**: **598 tests, 0 failures, 0 errors,
  3 skips, 120.802 s**. The skips are the two existing browser-dependent checks
  and Studio's positive preview-identity check.
- Focused `test_studio_*.py` suite in the lane worktree: **37 tests, 0 failures,
  0 errors, 1 skip, 22.121 s**. The skip is the same preview-identity boundary.
- Mock proof: self-approval refused; no remote calls for the initial private
  review request; author/reviewer credentials separated; selected editorial tree
  only; no `draft/*` transport; red local/public checks stop before exposure/merge;
  missing protection and ruleset refusal stop merge; no credential substitution;
  lost push/PR/review/merge responses reconcile after DB restart without duplicate
  writes; unknown writes without observed remote evidence stay unresolved;
  restart at every persisted phase; wrong live identity stays unverified;
  correction/withdrawal processing with the jobs directory read-only; publication
  checking does not block another piece's autosave.
- Real entrypoint: non-loopback bind exited **2** before creating data;
  `ss -ltn` showed exactly **one `127.0.0.1:8447` listener**;
  unauthenticated `/api/pieces` returned **401**. The test service was stopped.
- Actual `bash studio/host-ops/backup.sh --drill` restored **2 fixture pieces and
  3 checkpoints**, listed them through authenticated HTTP, and verified exact
  documents/cursors, including an uncommitted autosave after the last checkpoint.
  Backup/restore corruption rejection and account-hash preservation also pass.
- Python compilation and `git diff --check`: PASS.
- Tracked-file `NO_MACHINE_PATHS` check: PASS. Source scan under `studio` has no
  forbidden host roots or tailnet hostname. Generated bytecode is not source.

Logs remain ignored under `_audit/studio-a2`: `full-suite-accepted.log`,
`focused-accepted.log`, plus intermediate failure/mechanism evidence. They are
claims/evidence for replay, not a substitute for Claude's independent run.

## Reproduction and continuation

With a normal temporary directory outside the checkout:

```sh
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests -p 'test_studio_*.py' -v
python3 -m unittest tests.test_studio_preview.PreviewIdentity -v
python3 -m compileall -q studio tests/test_studio_*.py tests/harness/mock_github.py
git diff --check
python3 -c 'from pathlib import Path; from tools.gates.no_machine_paths import check_repo; print(check_repo(Path.cwd()))'
```

The literal direct script invocation of `tools/gates/no_machine_paths.py` is
not an executable gate on this base: it has package-relative imports. The
function invocation above and the full publication-gate tests execute the real
check without altering it.

For a sandbox confined to the worktree, clone the committed lane into an ignored
verification directory and put `TMPDIR` alongside that clone, not within it;
existing refresh oracles copy the source checkout. Host replays may use the
ordinary external temporary directory.

Follow `studio/host-ops/RUNBOOK.md` for environment provisioning, account creation,
loopback/tailnet probes and the adjusted backup-drill command. The environment
must supply data/repo/backup paths and the origin/session key. Nothing was
installed or scheduled by this lane.

Integrate A1/B and L11 before claiming acceptance. Require the positive HTTP
byte-identity test to execute with **no skip**, reconcile slot identifiers
(`lead`, `essays`, `briefs`, `notes`) with the integrated issue contract/UI,
exercise the real candidate gates, inspect final browser frames, and complete
Javier/Matías's human journey. Credentials, CODEOWNERS/ruleset behavior, rollback
dispatch permission and the actual tailnet remain externally unverified.

Live publication stays disabled by default and awaits L11 plus operator Q1/Q5.
English originals remain the default until Q2 is adopted in policy. The live
oracle implements the specified article-ID check; it does not claim independent
revision-content freshness for a correction that retains the same piece ID.
An ambiguous effect without positive remote evidence needs inspection before
its intent can be cleared. Never clear that state merely to retry or change
credentials. No desk ledger was written.

Resumen: A2 implementa el servidor privado y prueba el flujo contra el mock;
598 pruebas pasan sin fallas ni errores, con 3 omisiones explícitas. La identidad
de la vista previa, la inspección visual y la producción real esperan la
integración y verificación externa. No se hizo push ni publicación en vivo.
