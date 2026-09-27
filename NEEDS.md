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
