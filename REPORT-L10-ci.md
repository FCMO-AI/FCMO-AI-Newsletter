# L10-ci report

## Delivered

- Added a GitHub Actions workflow that builds the publication candidate on relevant pull requests and `main` changes, runs the 13 existing release gates, then runs the browser matrix before reporting success.
- Added a Playwright oracle that consumes the generated route manifest, covers all generated locale routes plus the shared 404 page at `390×844` and `1440×900`, and fails for browser console errors, horizontal overflow, same-origin request failures, broken images, absent/empty h1 elements, or broken internal links.
- Reused the repository's shared Playwright launcher, page/error collector, and Pages-compatible local server. The link sweep rewrites published internal URLs to the local candidate and does not visit third-party links.
- Added a seeded overflow browser fixture. It runs automatically when Playwright and Chromium are installed.

## Evidence

- Red-first commit: `a463361 test: specify the all-routes CI visual gate`; the new contract test failed because the oracle and workflow did not yet exist.
- `python3 -m unittest discover -s tests`: 563 tests, 0 failures/errors, 3 skipped. The browser fixture and existing browser-dependent tests skip because Playwright/Chromium is absent here.
- Candidate build from this branch produced 459 manifest routes. `python3 tools/gates/run_all.py .ci-visual-candidate`: all 13 gates passed, including `NO_FCMO_GROUP`. The temporary build directory was removed.
- Python compilation, both browser-oracle JavaScript syntax checks, workflow YAML parsing, and `git diff --check` passed.
- Attempting `python3 tests/oraculos/verificar_ci_visual.py .ci-visual-candidate` returned `BROWSER_UNAVAILABLE`; this container has neither a resolvable Playwright package nor Chromium. Therefore the full browser sweep, green local candidate run, and seeded-overflow red run remain for the architect's host with Chromium.

## Host continuation

After the normal Pages build creates `publish/`, run:

```sh
python3 tests/oraculos/verificar_ci_visual.py publish
python3 -m unittest discover -s tests
```

The second command includes the seeded fixture and must report it as an executed test (not skipped) on the host with Playwright available. The workflow installs the pinned Playwright 1.63.0 and Chromium and applies the same oracle to its candidate.

Estado: gates estáticas y suite aprobadas; la comprobación visual real queda pendiente de ejecutarse en el host con Chromium.
