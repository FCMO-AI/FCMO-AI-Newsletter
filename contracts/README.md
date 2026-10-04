# Contracts

This directory is the single source of truth for every data format exchanged
between the newsroom's tools, workflows and pages. Tools implement these
contracts; they do not define formats of their own. A change to a format is a
change here first, with its fixture, and only then in code.

- Schemas are JSON Schema (draft 2020-12 subset) and are **closed**: unknown
  properties are errors. `tests/harness/validate.py` checks them with the Python
  standard library only.
- `thresholds.json` holds every number the rules below use. Tools read it
  instead of hard-coding limits.
- `fixtures/` holds real snapshots of the corpus plus hand-checked examples of
  every format, valid and invalid. `fixtures/MANIFEST.json` lists each file and
  what it must do.
- `tests/harness/oracles.py` is the executable reference for the two stateful
  rules here: the wire state machine and the corpus guard. If this README and
  the oracle ever disagree, that is a contract bug, not a choice.

## Status

| Contract | File | Status | `schema` value |
|---|---|---|---|
| Wire status (bridge output) | `wire-status.schema.json` | v2-frozen | `fcmo-wire-status-v1` |
| Newsroom status (public) | `newsroom-status.v2.schema.json` | v2-frozen | `fcmo-newsroom-status-v2` |
| Publication freshness (public) | `publication-status.v1.schema.json` | v1-frozen | `fcmo-publication-status-v1` |
| Health state (operator) | `health-state.schema.json` | v2-frozen | `fcmo-health-state-v1` |
| Tombstones | `tombstones.schema.json` | v2-frozen | `fcmo-tombstones-v1` |
| Corpus guard report | `corpus-guard.report.schema.json` | v2-frozen | `fcmo-corpus-guard-report-v1` |
| Carried records (one line) | `corpus-carried.schema.json` | v2-frozen | (jsonl line) |
| First-publication ledger | `first-published.schema.json` | v2-frozen | `fcmo-first-published-v1` |
| Development record v3 | `record.v3.schema.json` | v2-frozen | `record_schema: fcmo-record-v3` |
| Site configuration | `site-config.schema.json` (+ `../config/site.json`) | v2-frozen | `fcmo-site-config-v1` |
| Thresholds | `thresholds.json` | v2-frozen | `fcmo-contract-thresholds-v1` |
| Story layer v2 | `stories.v2.schema.json` | **v2-draft** | `fcmo-stories-v2` |
| Locale overlay v2 | `locale-overlay.v2.schema.json` | **v2-draft** | `fcmo-locale-overlay-v2` |
| Airlock v2 (upstream) | `airlock.v2.schema.json` | observed | `fcmo-newswire-airlock-v2` |
| Development record v2 (upstream) | `record.v2.schema.json` | observed | (none) |

- **v2-frozen**: the format the liveness and integrity repair ships with.
  Changing it needs a new version (new `schema` value) or an additive optional
  field with a fixture.
- **v2-draft**: needed by the site rebuild; it may still be amended once, while
  that rebuild is implemented, and is frozen when the rebuild ships. Producers
  and consumers must validate against the current file, not a copy.
- **observed**: the upstream formats as they arrive today. They are lenient on
  purpose (they describe, they do not judge) and are used to validate the corpus
  fixtures and incoming snapshots before normalization.

Every schema carries `"x-contract": {"name", "status", "version"}`.

## Conventions

- **Timestamps** are UTC with second precision: `YYYY-MM-DDTHH:MM:SSZ`. Upstream
  values with fractions or offsets are truncated, never rounded
  (`2026-09-14T02:48:13.997038+00:00` becomes `2026-09-14T02:48:13Z`).
- **Time source.** Every time-dependent tool accepts `--now ISO8601`; otherwise
  it reads the `FCMO_NOW` environment variable; otherwise the real clock. Tests
  use `tests/harness/clock.py` (`FakeClock`).
- **Local dates.** Edition dates and story URL dates are calendar dates in
  `America/Mexico_City` (UTC-6 all year since 2022).
- **IDs.** Public story IDs match `^FCMO-[0-9A-F]{12}$` and never change or get
  reused.
- **Codes, not text.** Every reason, error or probe field is an upper-case code
  (`^[A-Z][A-Z0-9_]*(:[A-Z0-9_]+)?$`). Logs, stack traces, paths, credentials
  and personal data never appear in any contract file. Everything here is
  public.
- **Taxonomy** (closed): beats `technology, business, policy, society,
  research`; desks `architectures_scaling, reasoning_posttraining,
  agents_memory, multimodality_world_models, evaluation_science,
  compute_inference, labs_industry, policy_geopolitics`; confidence `confirmed,
  strongly_supported, supported, supported_with_limits, claimed_unverified`;
  claim labels `DEMONSTRATED, CLAIMED, INFERRED, SPECULATIVE, DISPUTED` with an
  optional upper-case `qualifier`; localization states `NATIVE_ARB,
  MACHINE_REVIEWED, PENDING, FAILED`.
- **Locales.** `en` is canonical; `es-419` and `zh-Hans` are the published
  translations. URL prefixes and Open Graph locales come from
  `config/site.json`, which is also the only place the base URL lives.

## Corpus layout

`corpus/` mixes two kinds of files, and tools must treat them differently.

| Owner | Files | Rules |
|---|---|---|
| Upstream (sealed) | `airlock.json`, `archive/YYYY/MM/DD/PUBLICATION.json`, `data/**` | Arrive only through the airlock; covered by the corpus digest and the sealed-file verification. Never edited here. |
| Newsroom | `wire-status.json`, `tombstones.json`, `carried.jsonl`, `first-published.json` | Written by newsroom tools; **excluded** from the content digest and from sealed-file allowlists, so writing them never changes the release id or fails verification. |

## Wire status

`corpus/wire-status.json` (schema `wire-status.schema.json`) is written by the
newswire bridge on **every** run, whether or not the content changed. It is
the liveness heartbeat; `airlock.json.generated_at` is not a heartbeat and no
check may use it as one.

What the bridge writes:

- `run_at`, `run_id`, `trigger`, `drill`.
- `transport` (`OK` when this run fetched, checked and verified a snapshot;
  otherwise `FAIL` with a `transport_error` code) and `last_transport_ok_at`.
- The upstream view: `source_mode` (`MAIN`, `CHECKPOINT` or `NONE`), `arb_main`
  (`GREEN`, `RED`, or `UNKNOWN` only before the first successful run),
  `arb_main_failures` (codes), `checkpoint_at`.
- The content view: `release_id`, `corpus_digest`, `record_count`,
  `release_changed`, `last_release_change_at`, `last_new_story_at` (the last
  time a new public id entered the live set), `newest_event_at`.
- The optional publication-authority view: `publication_authority` plus
  `last_authoritative_publication_date`,
  `last_authoritative_publication_at`, `last_authoritative_edition_id` and
  `last_authoritative_publication_status`. These fields are projected only
  from the newest valid transported
  `archive/YYYY/MM/DD/PUBLICATION.json`. A newly written status without a
  receipt says `publication_authority: UNKNOWN` and carries no authoritative
  fields. `airlock.json.generated_at`, edition HTML, `DAILY_BRIEF.md`, release
  changes and Newsletter ledgers are never publication authority.
- The guard result (`guard`).
- The bridge's own classification (`state`, `previous_state`, `state_since`)
  and `warnings`.

On `transport: FAIL` every upstream, content and authoritative-publication
field carries the values of the last OK run.

**Commit rule.** The bridge commits `wire-status.json` when `state` changes,
when the release changes, or when at least `commit_every_h` (5 h) have passed
since the last committed `run_at`. The margin is chosen so that with hourly
schedules and runner delays the committed file is never much more than 6 h old.

### States and decision table

Readers (preflight, freshness checks, the health job, the page builder)
classify the file at their own `now`. The bridge uses the same table for its
`state` field, except that it can never write `TRANSPORT_DOWN`, which only a
reader can observe. Rules are evaluated in order, and the first match wins.
Ages are `now − timestamp` in hours.

| # | Condition | State | Reason |
|---|---|---|---|
| R1 | file missing | `TRANSPORT_DOWN` | `WIRE_STATUS_MISSING` |
| R1 | file does not validate | `TRANSPORT_DOWN` | `WIRE_STATUS_INVALID` |
| R1 | `run_at` more than `future_skew_tolerance_min` (15 min) in the future | `TRANSPORT_DOWN` | `CLOCK_SKEW` |
| R1 | age of `run_at` > `transport_down_after_h` (30 h) | `TRANSPORT_DOWN` | `WIRE_STALE` |
| R2 | `transport = FAIL` and `last_transport_ok_at` is null or older than `transport_fail_grace_h` (6 h) | `DELAYED:TRANSPORT_FAIL` | `TRANSPORT_FAIL` |
| – | `transport = FAIL` within the grace period | continue with the carried fields | |
| A1 | authoritative receipt and `arb_main = RED` | `DELAYED:ARB_MAIN_RED` | `ARB_MAIN_RED` |
| A2 | authoritative receipt and `source_mode ≠ MAIN` | `DELAYED:CHECKPOINT_STALE` | `CHECKPOINT_STALE` |
| A3 | authoritative receipt and `guard.verdict = REGRESSION_REFUSED` | `DELAYED:SNAPSHOT_REFUSED` | `SNAPSHOT_REFUSED` |
| A4 | authoritative receipt status `PUBLISHED` and age of its `published_at` ≤ `fresh_new_story_max_h` (24 h) | `FRESH` | – |
| A5 | authoritative receipt status `QUIET` and age of its `published_at` ≤ `fresh_new_story_max_h` (24 h) | `QUIET` | – |
| A6 | an authoritative receipt exists but is older than 24 h | `DELAYED:STORY_SUPPLY` | `STORY_SUPPLY` |
| L1 | no authoritative receipt, `source_mode = MAIN`, and age of `last_new_story_at` ≤ 24 h | `FRESH` | – |
| L2 | no authoritative receipt and `arb_main = RED` | `DELAYED:ARB_MAIN_RED` | `ARB_MAIN_RED` |
| L3 | no authoritative receipt and `source_mode ≠ MAIN` | `DELAYED:CHECKPOINT_STALE` | `CHECKPOINT_STALE` |
| L4 | no authoritative receipt and `guard.verdict = REGRESSION_REFUSED` | `DELAYED:SNAPSHOT_REFUSED` | `SNAPSHOT_REFUSED` |
| L5 | no authoritative receipt and age of `last_new_story_at` ≤ `quiet_max_h` (96 h) | `QUIET` | – |
| L6 | no authoritative receipt and no earlier legacy rule matches | `DELAYED:STORY_SUPPLY` | `STORY_SUPPLY` |

The `L*` rules are the compatibility path for already transported releases
that predate `publication-receipt.v1`; their state behavior is unchanged. Once
a receipt exists, only A1–A6 decide FRESH/QUIET/delay. The 24-hour
age is the existing default, not a decision about the final daily cutoff or
weekend cadence.

Consequences:

- `FRESH` and `QUIET` are healthy. A quiet stretch with a green, reachable
  upstream is not an outage. Publication-freshness checks exit 0 only for
  these two states and exit 1 for every `DELAYED:*` and for `TRANSPORT_DOWN`.
- Serving checks (is the site up, and does it serve the release it claims?) do
  not look at freshness at all. A `DELAYED` newsroom is up.
- A red upstream is reported as its root cause (`ARB_MAIN_RED`), not as its
  symptoms (checkpoint, no new stories).

Boundary examples at the fixture reference time (`2026-09-26T20:00:00Z`):

| Input | `now` | Result |
|---|---|---|
| `wire-status.quiet.json` (`run_at 19:52`, last new story `2026-09-23T11:32:15Z`, 80.5 h) | reference | `QUIET` |
| same | `2026-09-27T11:32:15Z` (exactly 96 h) | `QUIET` |
| same | `2026-09-27T11:32:16Z` | `DELAYED:STORY_SUPPLY` |
| same | `2026-09-28T01:52:00Z` (`run_at` + 30 h) | `DELAYED:STORY_SUPPLY` |
| same | `2026-09-28T01:52:01Z` | `TRANSPORT_DOWN` (`WIRE_STALE`) |
| same | `2026-09-26T19:36:59Z` (`run_at` 15 min 1 s ahead) | `TRANSPORT_DOWN` (`CLOCK_SKEW`) |
| `wire-status.fresh.json` (new story at `19:10`) | `2026-09-27T19:10:00Z` | `FRESH` |
| same | `2026-09-27T19:10:01Z` | `QUIET` |
| `wire-status.delayed.json` (checkpoint, main red) | reference | `DELAYED:ARB_MAIN_RED` |
| `wire-status.down.json` (`run_at 2026-09-25T13:00:00Z`, 31 h) | reference | `TRANSPORT_DOWN` (`WIRE_STALE`) |
| quiet fixture with `transport FAIL`, last OK `14:00:00Z` | `2026-09-26T20:00:00Z` | `QUIET` (within grace) |
| same | `2026-09-26T20:00:01Z` | `DELAYED:TRANSPORT_FAIL` |

Warnings the bridge records: `ARB_MAIN_RED`, `CORPUS_CARRY_FORWARD`,
`SNAPSHOT_REFUSED`, `TRANSPORT_FAIL`.

### Drills

`workflow_dispatch` input `drill`:

- `force_checkpoint`: the run behaves as if main were red. It serves the
  checkpoint, writes `arb_main: RED` with a `DRILL_*` failure code and sets
  `drill`. The resulting `DELAYED` state is visible end to end.
- `regressing_snapshot`: the run feeds the guard a candidate that drops more
  than the refusal ratio. It must record `REGRESSION_REFUSED` and commit
  nothing but `wire-status.json`.

Drill runs always set `drill`, and `newsroom-status.json` copies it, so a drill
is never mistaken for an incident.

## Newsroom status

`site/data/newsroom-status.json` (schema `newsroom-status.v2.schema.json`) is
the public, reader-facing status. The refresh job writes it on every run, even
when no page changes. Pages must not cache it for more than 300 s
(`status_cache.newsroom_status_max_cache_s`).

| Field | Rule |
|---|---|
| `status_updated_at` | time of this refresh run |
| `wire_state`, `wire_run_at` | reader classification of `wire-status.json` at `status_updated_at`, and its `run_at` |
| `edition_state` | `FRESH`, `QUIET`, `DELAYED` or `TRANSPORT_DOWN` (the part of `wire_state` before `:`) |
| `edition_reason` | null for `FRESH` and `QUIET`; the `DELAYED` reason; or the `TRANSPORT_DOWN` cause |
| `edition_date` | Mexico City date of `status_updated_at` |
| `last_edition_at` | when the served release last changed (`last_release_change_at`) |
| `quiet_since` | `last_new_story_at` when `QUIET`, otherwise null ("no material changes since") |
| `release_id`, `corpus_digest`, `live_story_count` | the release being served |
| `translation` | per locale: `complete`, `pending`, `failed` counts of (story, locale) pairs |
| `drill` | copied from the wire status |
| `alerts` | codes of open alerts, for the status page |

The legacy fields of the v1 file remain allowed (optional) while old readers
exist.

Reader banner. `DELAYED` and `TRANSPORT_DOWN` show a banner in all three
languages with `last_edition_at`. As a fail-safe, the page script also shows it
when `status_updated_at` is older than `reader_stale_banner_after_h` (36 h),
whatever `edition_state` says, because an old status file means the refresh
itself stopped.

### Publication freshness (L3)

`status.json` is the primary machine-readable reader status. Its closed,
versioned contract is `publication-status.v1.schema.json`. The same object is
an additive optional `publication_status` field on the frozen v2 newsroom
receipt. Existing transport fields and wire health classification retain their
meaning; reader banners and status chips use the publication projection.

- `FRESH`: wire is FRESH and the newest live material is at most 48 hours old.
- `QUIET`: wire is QUIET and the newest live material is at most 48 hours old.
- `DELAYED`: either condition is unproven. Preserve the wire failure reason,
  otherwise use `STORY_SUPPLY`; future dates beyond 15 minutes use `CLOCK_SKEW`.
- News age uses the existing v4 chronology: the earlier of `event_at` and
  `first_published_at`. Rebuilds, edits and the immutable airlock `generated_at`
  never renew news age. `last_edition_at` in the projection is the newest stored
  Story first-publication date, including withdrawn/merged history; this is
  publication metadata, not proof of a live deployment.
- `checked_at` is the reference instant; JSON consumers must inspect it before
  trusting a static status as current. No network or model call runs on a page
  view. The existing reader-clock safeguard remains in place.

Refresh preflight exits 0 for a classified outage as well as a healthy wire,
allowing an already accepted corpus to be rebuilt and its warning published.
Malformed/missing corpus or an unsupported airlock schema still exits 2.
This is construction availability, not health: `wire_status.py classify` and
`editorial_freshness.py check` keep their failing health exit codes. The latter
measures event age even when the wire reports FRESH or QUIET (36-hour alarm).
Age-only changes wait for the existing five-hour status cadence; a change in
reader state, reason or news identity is recorded immediately.

## Health state

`health-state.json` (schema `health-state.schema.json`) is produced by the
hourly health job and uploaded as an artifact. The operator status page is
generated from it.

| Signal | Required | GREEN when | RED codes |
|---|---|---|---|
| `serving` | yes | every checked route answers 200 and the live release matches the deployed identity | `UNREACHABLE`, `ROUTES_FAILED`, `IDENTITY_MISMATCH` |
| `transport` | yes | the wire state is not `TRANSPORT_DOWN` or `DELAYED:TRANSPORT_FAIL` | `TRANSPORT_DOWN`, `TRANSPORT_FAIL` |
| `upstream` | yes | wire state `FRESH` or `QUIET` (code `FRESH` / `QUIET`) | `ARB_MAIN_RED`, `CHECKPOINT_STALE`, `STORY_SUPPLY`, `SNAPSHOT_REFUSED` |
| `editorial` | yes | the newest story event is at most `newest_event_max_age_h` (36 h) old | `EVENT_STALE`, `STORY_SUPPLY` |
| `translation` | no | no pair pending beyond its grace | `BACKLOG` |
| `community` | no | the membership site answers | `DOWN` (or `NOT_CONFIGURED`) |
| `watchdog` | no | the external watchdog reported recently | `STALE` (or `NOT_CONFIGURED`) |

- A signal that cannot be measured is `UNKNOWN`, which counts as not GREEN.
  For example, `upstream` is `UNKNOWN` while the transport is down.
- `overall` is `RED` exactly when a required signal is not `GREEN`. The schema
  enforces this.
- `open_alerts` has at most one entry per key (`overall` or a signal name). An
  alert opens when its key turns non-GREEN and closes when it turns GREEN;
  `since` is the transition time. Informational signals are reported but never
  make `overall` red.

## `tools/corpus_guard.py`

The guard decides whether a candidate snapshot may replace the published
corpus. It works per record: one missing story never blocks new stories.

### Synopsis

```
python3 tools/corpus_guard.py check --published P --candidate C
        [--tombstones T] [--max-missing-ratio 0.20] [--report OUT.json] [--now ISO8601]

python3 tools/corpus_guard.py apply --published P --candidate C --out DIR
        [--tombstones T] [--max-missing-ratio 0.20] [--report OUT.json] [--now ISO8601]
```

- `P` and `C` are corpus directories (`data/developments.jsonl`, and for `P`
  also `carried.jsonl` when present) or `.jsonl` files.
- `T` defaults to `<P>/tombstones.json` when that file exists.
- `--max-missing-ratio` defaults to `corpus_guard.max_missing_ratio` in
  `thresholds.json`.

### Set algebra

```
already_withdrawn = ids in P whose record status is withdrawn or superseded
live       = (ids in P ∪ ids in P/carried.jsonl) − already_withdrawn
tombstoned = ids of tombstones with reinstated_at = null
upstream_w = ids in C whose record status is withdrawn or superseded
withdrawn  = live ∩ (tombstoned ∪ upstream_w)     (source: tombstone wins over upstream)
missing    = (live − ids in C) − withdrawn
ratio      = |missing| / |live|                   (rounded to 4 decimals; 0 when live is empty)
added      = ids in C − live − tombstoned − upstream_w
suppressed = (ids in C ∩ tombstoned) − live       (tombstoned ids that reappear stay out)
```

### Verdicts and exit codes

| Verdict | When | Exit | Effect |
|---|---|---|---|
| `REGRESSION_REFUSED` | `ratio > max_missing_ratio` | 3 | The snapshot is refused and nothing is written. The previous release keeps serving, and the wire state becomes `DELAYED:SNAPSHOT_REFUSED`. |
| `CARRY_FORWARD` | at least one missing id, ratio within the limit | 0 | New and updated stories publish. Each missing id stays live from its last published record (`carried.jsonl`, `carried_forward: true` in the story layer), and an alert is raised. |
| `OK` | no missing ids | 0 | Normal publish. |
| (usage) | bad arguments, unreadable or invalid input | 2 | Nothing is written. |

- A withdrawn id is never "missing". It leaves the live set with its
  correction, from `tombstones.json` or from an upstream `withdrawn` or
  `superseded` record, which needs no human.
- A missing id without a tombstone is never dropped silently. It is carried
  and alerted until it comes back or someone tombstones it.

### Output

The first stdout line is exactly:

```
<VERDICT> missing=<id,id|-> withdrawn=<id,id|-> added=<n> published=<|live|> candidate=<|C|> ratio=<r with 4 decimals>
```

Alerts go to stderr, one line each:

```
ALERT CORPUS_CARRY_FORWARD missing=<ids>
ALERT CORPUS_REGRESSION_REFUSED missing=<n> ratio=<r>
```

`--report` writes `corpus-guard.report.schema.json`. The report holds ids,
counts and codes only, never paths.

`apply` runs `check` first. On `OK` or `CARRY_FORWARD` it writes the
candidate corpus to `DIR` with `DIR/carried.jsonl`. This file holds the missing
ids with their last published record (`corpus-carried.schema.json`). It keeps
`carried_since` for ids that were already carried and drops ids that
reappeared or were withdrawn. On `REGRESSION_REFUSED` it writes nothing and
exits 3.

### Examples (real corpus history, see fixtures)

| Published → candidate | Tombstones | First line | Exit |
|---|---|---|---|
| corpus-44 → corpus-43 | none | `CARRY_FORWARD missing=FCMO-FDBE3D996243 withdrawn=- added=0 published=44 candidate=43 ratio=0.0227` | 0 |
| corpus-44 → corpus-43 | `fixtures/tombstones.json` | `OK missing=- withdrawn=FCMO-FDBE3D996243 added=0 published=44 candidate=43 ratio=0.0000` | 0 |
| corpus-43 → corpus-27 | none | `REGRESSION_REFUSED missing=<16 ids> withdrawn=- added=0 published=43 candidate=27 ratio=0.3721` | 3 |
| corpus-43 → corpus-44 | none | `OK missing=- withdrawn=- added=1 published=43 candidate=44 ratio=0.0000` | 0 |

The expected reports are `fixtures/corpus-guard.{carry-forward,withdrawn,refused,added}.json`.

## Tombstones, carried records and the first-publication ledger

- `corpus/tombstones.json` is **append-only**. Entries are never deleted.
  Reinstating a story sets `reinstated_at`. Every entry has a reader-facing
  `correction` (English required; Spanish and Chinese when available, otherwise
  those pages link to the English correction). `decided_by` is a role
  (`operator`, `upstream`, `editorial_policy`), never a person's name.
- `corpus/carried.jsonl` is owned by the guard (see `apply`).
- `corpus/first-published.json` freezes, per id, `first_published_at` (from
  the git history of the published story data), the Mexico City `url_date` and
  the `slug`. A story URL (`/{locale prefix}/YYYY/MM/DD/{slug}/`) never changes
  once published. A merged story keeps its entry with `redirect_to`.

## Story layer and locale overlay (drafts)

- `stories.v2`: one entry per public id. This includes withdrawn and merged
  ids, which change status and never disappear. The reader-facing date is
  `event_at` at its `date_precision`, with `first_published_at` as the second
  line. `front_page_eligible` needs a written `headline` (≤ 90 characters) and
  `dek` (≤ 240). Titles are never truncated to fit. Each (story, locale) pair is
  complete (`NATIVE_ARB` or `MACHINE_REVIEWED`, with `missing` empty) or visibly
  pending. A pending or failed pair renders as a notice with a link to English,
  never as English prose under a non-English `lang`.
- `locale-overlay.v2`: the normalized per-locale overlay keyed by id.
  `source_sha256` is the SHA-256 of the canonical JSON (sorted keys,
  `ensure_ascii=False`, separators `,` and `:`) of the English record's prose
  keys (`title, summary, why_it_matters, why, importance_rationale,
  limitations, contradictory_evidence, claims, evidence_gaps, relationships,
  technical`, those present). When the English record changes, the pair
  becomes `PENDING` again. Upstream-authored fields win over machine fields;
  machine fields carry provenance (model, prompt and glossary hashes,
  `human_reviewed`).

## record.v3

This is the normalized record: closed enums, a `beat` plus desks, an optional
upstream `headline` and `dek`, `kind: event` with `scheduled_at` for agenda
items, and a `withdrawal` block for withdrawn or superseded records. Records in
today's upstream format (`record.v2`) reach this shape through the taxonomy
normalization. Ingest validates each record on its own and quarantines failures
with a public reason instead of failing the batch.

## Fixtures

| Fixture | Source |
|---|---|
| `corpus-27/` | corpus at commit `d7d2942`: the 2026-09-18 regressing snapshot (27 records; 16 ids of corpus-43 absent) |
| `corpus-43/` | corpus at commit `70eade1`: the current production corpus |
| `corpus-44/` | corpus at commit `d7e68a0`: the last corpus that carried `FCMO-FDBE3D996243` |
| `wire-status.*`, `newsroom-status.*`, `health-state.*` | built for the reference time `2026-09-26T20:00:00Z` from those corpora |
| `stories.v2.json`, `locale-overlay.v2.es-419.json`, `record.v3.*` | derived from corpus-44 and the upstream locale deltas. Headlines, deks and their translations are fixture-authored, and so is the agenda event. |
| `first-published.json` | first appearance of each id in the history of the published story data |
| `invalid/*` | minimal negative cases; each must fail with the error in `MANIFEST.json` |

## Harness

```
python3 tests/harness/validate.py --all-fixtures            # every fixture, valid and invalid
python3 tests/harness/validate.py --check-schemas           # meta-check of the schemas
python3 tests/harness/validate.py SCHEMA FILE...            # one format
python3 tests/harness/serve.py --root DIR --base /FCMO-AI-Newsletter/ --port 8765
python3 tests/harness/mock_ghost.py --port 0                # Ghost Admin + Content API mock
NODE_PATH=<playwright install>/node_modules node tests/harness/browser/first_screen.mjs URL...
NODE_PATH=... node tests/harness/browser/overflow.mjs URL...
NODE_PATH=...:<axe-core install>/node_modules node tests/harness/browser/axe.mjs URL... [--min-font 12]
```

The browser scripts print one JSON report and exit 0 (pass), 1 (fail), or 2
(Playwright or axe-core not available). Exit 2 is never a pass.
