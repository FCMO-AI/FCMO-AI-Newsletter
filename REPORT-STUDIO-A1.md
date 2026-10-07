# Studio A1 — implementation report

Date: 2026-10-04 UTC
Branch: `c5/studio-a1`
Base: `a6275de`

## Outcome

Implemented the A1 content contract and static build integration for human essays, letters, notes, and curated issue records. The production paper build reads the closed `fcmo-piece-v1`, `fcmo-essay-doc-v1`, and `fcmo-issue-v1` formats; checks locale structure, citations, footnotes, figures, numeric and URL parity, and provenance; then renders through the shared document renderer and Lane B's `essay.render(...)` template when present. A deterministic fallback keeps the A1 build usable before B lands.

The output includes localized piece and issue pages, the letters shelf, RSS/Atom/JSON Feed entries, sitemap entries, local search, and `llms.txt`/`llms-full.txt` entries. Pending locales have an explicit pending page. Machine-prepared but unreviewed languages receive a disclosure and a link to the source language. Withdrawn pieces render a dated tombstone. Editorial source copying is allowlisted to validated records and referenced WebP figures.

The `PIECE_VALID` gate is the fourteenth release gate. It rejects unknown nodes, unsafe links, block/footnote/citation/figure mismatches, missing figure credit or locale alt/captions, dishonest review provenance, invalid issue references, and broken piece routes. Structured language quotations render `lang`, `translate="no"`, and `data-field="quotation"`; unmarked English prose still fails `ENGLISH_LEAK`.

## Red-first and commits

- `e854f16` — tests-only red-first commit. The initial run failed on the absent schemas and gate, unsupported editorial build input, and missing gate module.
- `d05095b` — A1 implementation. The final contract tests pass against the implementation.

## Verification

- `python3 -m unittest discover -s tests`: **572 tests, 0 failures, 0 errors, 2 skipped**.
- `python3 -m unittest tests.test_piece_contract tests.test_essay_build tests.test_piece_gate -v`: **11 passed**.
- `python3 tests/harness/validate.py --all-fixtures`: **55 fixtures passed**.
- Fixture paper build: **468 routes**; `tools/gates/run_all.py` reports **GATES PASS (14/14)**. English, Spanish, and Chinese piece routes exist. Checks cover RSS, Atom, JSON Feed, sitemap, local search, `llms.txt`, and `llms-full.txt` entries, as well as pending, withdrawn, and machine-prepared states.
- `NO_MACHINE_PATHS` passed in the 14-gate run and via `check_repo`; the scoped host-path grep returned no matches. `git diff --check` passed.

The spec's standalone invocation `python3 tools/gates/no_machine_paths.py` currently fails because that module uses a relative import when executed as a script. Its gate function passes through `run_all.py`, and the repository check was separately invoked through `check_repo`; I did not change the out-of-lane gate module.

## Scope and remaining boundary

- No live publication, push, deploy, or production freshness claim was made. Live publish remains out of scope until L11 and Q1/Q5.
- `.github/workflows/pages.yml` was left unchanged because its editorial path change is conditional on L11 merging.
- No browser, frame, visual, or human usability approval is claimed by A1.
- The final lane report itself is a reporting-only commit after `d05095b`; no external action was taken.

## Resumen

Studio A1 integra ensayos humanos con validación cerrada, renderizado localizado y 14 compuertas verdes; la suite completa pasó 572 pruebas con dos omisiones. No se publicó ni se verificó producción, y la activación pública sigue dependiendo de L11 y de Q1/Q5.
