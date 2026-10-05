# L3 — Supply-independent publication freshness

Local implementation on `c5/fresh`, based on v4/design commit `a6275de`. No push, merge, deployment, upstream repair, external network request or other worktree mutation was performed. These are local claims for independent host verification.

The accepted corpus can be rebuilt with a frozen or absent transport heartbeat. The public publication now exposes `status.json` with FRESH / QUIET / DELAYED and measures the actual age of live Story material rather than the immutable airlock generation time. Banners, reader status chips and status cards use that same projection in en, es-419 and zh-Hans, using existing curated copy. The three localized status pages advertise the JSON alternate. Deployment identity now also binds `status.json` among the critical files checked at the live origin, with compatibility for older LKGs that lack this endpoint. A substituted FRESH JSON fails the existing live-byte oracle in a controlled fixture.

The new closed contract is `contracts/publication-status.v1.schema.json`. It is also an optional additive `publication_status` object on the frozen newsroom v2 receipt; existing transport fields remain diagnostic and backward compatible. News age follows v4's event/first-publication chronology, excludes withdrawn/merged stories, and cannot be renewed by a rebuild or verification edit. The last-edition date uses stored Story first-publication history, including withdrawals and merges, rather than a newer seal date. This metadata does not claim that the edition was deployed.

Preflight now exits 0 after successfully classifying a transport outage; invalid corpus/airlock input still exits 2. This changes construction availability, not publication safety. Wire health still exits 1 on a down/stale transport. Editorial health now measures event age even on a FRESH or QUIET wire: stale news cannot obtain a green editorial signal merely from a working transport. Privacy, localization, digest/seal, immutable history and all 13 publication gates are preserved. No supplied news record, localization prose or release overlay was altered.

The reader-clock safeguard now uses the latest status check, retaining a legacy edition-date fallback. This prevents an old edition checked recently from becoming DELAYED merely because the edition date is old. The generated JavaScript was executed against both a recent-check and abandoned-check fixture; this is a script-mechanism check, not browser or visual proof. Status-only age changes retain the existing five-hour write cadence, while state/reason/news-identity changes write immediately.

## Red-first evidence

- `4fe45c4`: regression tests committed before implementation. Its minimal corpus fixture initially lacked the directory/index shape required by preflight.
- `d3e2b5f`: corrected the fixture while still red. The valid frozen-heartbeat fixture then returned 1 at preflight, public JSON was absent, publication age was absent from status-only refresh, and stale editorial content incorrectly passed with FRESH/QUIET transport. Four tests produced five failing assertions/subtests.
- An additional red test showed `status.json` was absent from deployment critical files before it was added.
- A further red check exposed the generated banner's missing status-check clock in all three states/locales before the safeguard was corrected.

## Local validation

- Baseline: 561 tests, 0 failures/errors, 2 skips.
- Final full suite: 572 tests in 117.870 seconds, 0 failures/errors, 2 skips (the baseline also had 2). No test-skip environment override was set.
- Lane regressions: 10 tests pass, including frozen-heartbeat CLI behavior, unchanged red wire health, stale content on healthy transport, exact 48-hour boundary, missing/future dates, upstream cause retention, unsupported supply schema preserving the prior status, and EN/ES/ZH banner parity.
- Deployment identity: 4 tests pass, including rejection of substituted public freshness JSON.
- Candidate: 459 routes; all 13 gates pass, including NO_FCMO_GROUP. The existing glossary warnings remain informational and were not suppressed or changed.
- Static HTML parsing checks every generated route: one visible DELAYED banner with the same check time as `status.json`, 153 routes in each locale. This proves source/DOM-attribute consistency, not browser layout.
- All 46 contract fixtures pass, including both the new public format and its additive newsroom-v2 embedding. The final candidate's `status.json` validates against the new schema.
- `build_ready_receipt.py --check` passes. The regenerated measured candidate has 1697 files and tree SHA-256 `a86c31ec7a27` (prefix).
- Committed check time: `2026-10-04T04:38:39Z` (real UTC clock). Public state DELAYED, reason WIRE_STATUS_MISSING; wire TRANSPORT_DOWN; newest live news time `2026-09-11T17:55:45Z`, age 538.715 hours; latest stored Story first-publication time `2026-09-18T22:36:23Z`.
- `git diff --check` passes. Browser rendering and production are unverified for the boundary below.

## Reproduce on the host

Run from this worktree/branch, with no test-skip environment override:

```sh
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests -p test_supply_independent_freshness.py
python3 tests/harness/validate.py --all-fixtures
python3 tools/build_ready_receipt.py --check
python3 tools/paper/build.py --stories site/data/stories.v2.json --status site/data/newsroom-status.json --out _audit/c5-fresh/host --base /FCMO-AI-Newsletter/
python3 tools/gates/run_all.py _audit/c5-fresh/host
python3 tests/harness/validate.py contracts/publication-status.v1.schema.json _audit/c5-fresh/host/status.json
python3 tests/oraculos/verificar_paper.py _audit/c5-fresh/host
```

Configure the host's existing Playwright/Chromium through `PLAYWRIGHT_MODULE` and `CHROME_PATH` for the final command. Inspect the DELAYED banner and status card on `/`, `/diario/`, `/status/` and their es/zh equivalents at 390 and 1440 pixels, plus representative Story pages. Check console errors, overflow, placement and localized copy. The local browser command returned `BROWSER_UNAVAILABLE` because Playwright was not installed; the historical shared screenshot-tool path in PLAN.md was also absent. No download was authorized in this lane. Visual correctness remains unverified here.

After independent host acceptance, integration/push and production verification belong to the architect/operator. The production check must fetch the deployed `status.json` and compare its state, news identity and check time with the reader-visible EN/ES/ZH banners. This lane does not establish unattended production cycles or repair news supply.

A later status-only refresh can be run with `python3 tools/newsroom_receipt.py status`; it records the real clock, does not re-date news, and does not assert new private-source research. Rebuild the candidate/receipt after changing a committed status snapshot. To undo this lane, revert its implementation and report commits together; do not revert only the status or its derived receipt.

Resumen: la frescura pública ya depende de las noticias reales y muestra DELAYED con el corpus actual. Falta la comprobación independiente en navegador y producción; no se hizo push.
