# Studio integration — verified HTTP path, frontend rebuild pending

2026-10-04 UTC · branch `c5/studio-int`.

## Outcome and boundary

Merged A2 (`b0167ae`) into A1 (`6a93224`), then B (`9091186`), in the requested order. Merge commits: `36e69df` and `207077f`. There were no file conflicts. A1 remains the content/build authority, A2 owns persisted state and publication, and B's CSS, reading template and visual composition are retained.

**The real loopback HTTP flow is verified. Full Studio UI acceptance is not established.** The isolated test creates a draft, saves through authenticated HTTP, previews through the production paper renderer, requests private review, rejects self-approval, accepts the other person's approval, builds a real local git candidate, runs all fourteen publication gates, and completes publication against the loopback GitHub/Pages mock. The test asserts the author owns the selected-tree transport and records three verified mock live URLs. It does not push to an external remote or prove live production.

The available npm cache lacks the locked ProseMirror/esbuild dependencies. `npm ci --offline --ignore-scripts --no-audit --no-fund` failed with `ENOTCACHED` (including `w3c-keyname`). Network use was prohibited by the campaign rules; no registry request in online mode was made. No other worktree was read or modified. A local dependency-cache path was requested, but none was supplied during this run.

Consequently, B's original committed `dist/` is **not rebuilt for the changed source**. Serving it would expose an incompatible editor. The server now refuses Studio chrome with HTTP 503 until `build.mjs` produces an integrity manifest matching the current source and artifacts. Private APIs and authenticated preview remain usable. This is a continuation-ready integration branch, **not a ready-to-use UI or a merge recommendation**. Rebuild, commit the regenerated `dist/`, and independently inspect the real browser path before accepting the integration.

## Changes

- Added the UI's source locale, per-language readiness/word counts, total words, dates and reviewer identity to real persisted API responses. Sources and figures remain the actual A2 API formats; the editor source now consumes them directly.
- Connected upload results and authenticated draft figure URLs; document/resource writes use the same revision sequence. Source records include publisher and omit an unset evidence class. List serialization conforms to A2's closed document model.
- Translation source hashes and authorship come from A2's private metadata; they are not injected into document attributes. Chinese review sends the required confirmation. Conflicts require an explicit choice. Translation controls preserve references and keep title/dek/footnotes editable.
- Added the deliberate readiness action for the original language. English remains the default until Q2 is adopted; the UI does not silently authorize a non-English original.
- Replaced the issue canvas's dev-only draft endpoint with real issue creation and revision-aware saving. The canonical A1 slots (`principal`, `essays`, `day-in-ai`, `notes`) are used by both server and UI. References use publication IDs; brief text stays read-only.
- Connected publication timeline/URLs and version comparison aliases to A2's actual responses.
- Draft preview uses the production `PaperBuilder`, document renderer and B template in a private snapshot. It does not change persisted readiness or provenance. Publication privacy checks still use a separate strict production build, so private draft preview cannot make a publication check green. Ready-piece HTTP preview remains byte-identical to a separate full build.
- Corrected the disclosure predicate: only an unreviewed assistant-origin language gets a machine-prepared notice. A human draft is not falsely described as machine-produced.
- Added source/artifact binding to the build and server; stale bundles are refused. Removed a forbidden host path from B's inherited report without weakening `NO_MACHINE_PATHS`.

There is no dev API, placeholder renderer, storage double or mocked checklist on the tested HTTP path. The GitHub/Pages transport is the mock. The candidate check in this isolated test executes the real paper build and fourteen gates; it deliberately does **not** pretend that the absent L11 `ops/publish.py --check` exists. The live default still requires L11, protected GitHub publishing and Q1/Q5; it remains disabled.

## Red-first evidence and local verification

- `84ff852`: the first integration regression failed with missing `/api/me.other` and HTTP 503 on draft preview.
- `f933e90`: the stale-bundle regression observed HTTP 200 before the fail-closed artifact guard. The gated HTTP publication proof is also banked in this commit.
- `python3 -m unittest discover -s tests`: **624 tests, no failures/errors, three skips, 157.940 s**. Two are existing browser-dependent checks; the third is the inapplicable absent-renderer negative test.
- Focused Studio suite: **41 tests, no failures/errors, one skip**. The skip is the absent-renderer negative test, which is inapplicable after integration.
- Positive HTTP preview identity: executed successfully; no integration skip is used for this proof.
- Integrated HTTP flow and stale-bundle isolation: **4 tests passed**.
- Real candidate: **GATES PASS (14/14)**, including `PIECE_VALID`, `NO_MACHINE_PATHS`, privacy and localization gates.
- Python compilation, JavaScript syntax checks and `git diff --check`: PASS.
- The disposable browser fixture seeder executes successfully against the real Store.
- Browser attempt: exit 2, `BROWSER_UNAVAILABLE` because Playwright is absent. No browser, overflow, accessibility, frames or visual approval is claimed.

Ignored local evidence: `_audit/studio-int/{red,bundle-red,accepted-e2e,focused-final,full-suite-final,preview-identity-final,candidate,browser-attempt}.log`.

## Exact host continuation commands

Run these from the root of this worktree. The account/data commands below create a **disposable local test store**, not a production service. Passwords are entered at the prompts and supplied to the browser harness through `STUDIO_PASS`; no production credential is needed. Set `PLAYWRIGHT_MODULE`, `CHROME_PATH` and `AXE_CORE_PATH` to installed host dependencies as required by the existing harness.

First rebuild and bank the browser artifact. This requires the locked dependencies in an authorized host cache or authorized host registry access:

```sh
cd studio/web
npm ci --ignore-scripts --no-audit --no-fund
node --test test/*.test.mjs
node build.mjs
cd ../..
git add studio/web/dist
git -c user.name=Codex -c user.email=noreply@openai.com commit -m 'build: regenerate integrated Studio browser bundle'
cd studio/web
node build.mjs
git diff --exit-code -- dist/
cd ../..
python3 -c 'from pathlib import Path; from studio.server.bundle import ready; assert ready(Path.cwd())'
python3 -m unittest discover -s tests
python3 -m unittest tests.test_studio_integration tests.test_studio_preview -v
```

The reproducibility comparison is against the **regenerated integration bundle**, not B's old bundle. Do not generate a manifest for unchanged stale bytes.

Start and probe the real port 8447, after the rebuild:

```sh
mkdir -p _audit/studio-int
export STUDIO_DATA="$PWD/_audit/studio-int/host-data"
export STUDIO_REPO="$PWD"
export STUDIO_ORIGIN=http://127.0.0.1:8447
export STUDIO_SESSION_KEY=disposable-host-test-session-key-000000000000
export STUDIO_PORT=8447
export STUDIO_LIVE_ENABLED=0
python3 -m studio.server --add-user javier
python3 -m studio.server --add-user matias
python3 -m tests.harness.seed_studio > _audit/studio-int/fixture-slug
export STUDIO_FIXTURE_SLUG="$(cat _audit/studio-int/fixture-slug)"
python3 -m studio.server > _audit/studio-int/host-server.log 2>&1 &
STUDIO_TEST_PID=$!
trap 'kill "$STUDIO_TEST_PID"' EXIT
ss -ltn | rg '127\.0\.0\.1:8447'
curl --fail --silent http://127.0.0.1:8447/healthz
curl --silent --output /dev/null --write-out '%{http_code}\n' http://127.0.0.1:8447/api/pieces
curl --silent --output /dev/null --write-out '%{http_code}\n' http://127.0.0.1:8447/
```

Expected: one loopback listener, `{"ok":true}`, 401 for the private API, 200 for rebuilt login chrome. The first failed bundle build instead yields 503 for chrome; that is a blocker, not a passing UI check. Check non-loopback rejection in a separate shell with the same disposable environment:

```sh
STUDIO_BIND=0.0.0.0 python3 -m studio.server
```

Expected exit code 2 before any listener is created.

With the disposable Javier password available in `STUDIO_PASS`:

```sh
STUDIO_USER=javier node tests/harness/browser/studio_editor.mjs http://127.0.0.1:8447/
STUDIO_USER=javier node tests/harness/browser/studio_translate.mjs http://127.0.0.1:8447/ "$STUDIO_FIXTURE_SLUG"
STUDIO_USER=javier node tests/harness/browser/studio_publish.mjs http://127.0.0.1:8447/ "$STUDIO_FIXTURE_SLUG"
STUDIO_USER=javier STUDIO_SLUG="$STUDIO_FIXTURE_SLUG" node tests/harness/browser/studio_a11y.mjs http://127.0.0.1:8447/ --viewport 390x844 --viewport 1440x900
STUDIO_USER=javier STUDIO_SLUG="$STUDIO_FIXTURE_SLUG" STUDIO_ESSAY_SLUG=fixture-essay node tests/harness/browser/studio_frames.mjs http://127.0.0.1:8447/ http://127.0.0.1:8848/ _audit/studio-int/frames
```

Run the frame command after starting the paper server below. It does not click approval or cause publication. The isolated seed provides a writer view of review/progress; repeat those two screens as the other account during a permitted mock publication flow to inspect the populated timeline. The fixtures are local test prose. B's old dev-mock frames do not establish the integrated UI's appearance. Inspect the newly produced frames at 390/1440, light/dark and all three languages, then obtain the required Sonnet/Opus visual review. The detailed scripts may expose further UI defects; none has been reported green here.

Check the built essay pages independently:

```sh
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --editorial tests/fixtures/editorial --out _audit/studio-int/paper --base /
python3 tools/gates/run_all.py _audit/studio-int/paper
python3 -m http.server 8848 --bind 127.0.0.1 --directory _audit/studio-int/paper > _audit/studio-int/paper-server.log 2>&1 &
STUDIO_PAPER_PID=$!
node tests/harness/browser/overflow.mjs http://127.0.0.1:8848/cartas/fixture-essay/ http://127.0.0.1:8848/es/cartas/fixture-essay/ http://127.0.0.1:8848/zh/cartas/fixture-essay/ --viewport 390x844 --viewport 1440x900
node tests/harness/browser/axe.mjs http://127.0.0.1:8848/cartas/fixture-essay/ http://127.0.0.1:8848/es/cartas/fixture-essay/ http://127.0.0.1:8848/zh/cartas/fixture-essay/
kill "$STUDIO_PAPER_PID"
```

The A1 fixture deliberately has a pending Chinese route. Inspect that as a pending page; also repeat with a genuinely ready three-language article before claiming language-complete visual acceptance.

Remaining production-only boundaries: host backup/restore drill from `studio/host-ops/RUNBOOK.md`, actual tailnet reachability/isolation, Q1/Q2/Q5 decisions, L11's full check command/CODEOWNERS/ruleset/deploy trigger, real GitHub review and merge, production-origin visibility, and Javier/Matías's timed phone journey. These require the responsible host/operator lane and are not authorized external effects in this integration task.

## Resumen

A1, A2 y B están integradas y el flujo HTTP completo pasa con las 14 compuertas reales y publicación simulada. La interfaz sigue pendiente de reconstrucción y revisión en navegador; el servidor impide abrir el bundle antiguo. No se hizo push, instalación ni publicación real.
