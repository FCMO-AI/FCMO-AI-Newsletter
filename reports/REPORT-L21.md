# L21 — why newer stories do not reach the newspaper

As of 2026-10-05 05:35 UTC. Branch `c5/fresh2`, starting at public commit `3bdf00e`. No push, remote mutation, ARB mutation, main/origin update or other-worktree write. Claims await Claude's independent host rerun.

**Cause:** the only two recently promoted developments carry `event_date` but `event_at: null`. ARB's query projection discards the alternate date. Both records cross the sanitized bridge, then Newsletter correctly quarantines them. A green ARB main, recent seal or new edition receipt does not repair this. Most intake remains unpromoted. Separately, serving health checks the retired SPA's name/routes after deployment of the paper SSG.

## Evidence boundary

Read the required runtime/disciplines, repository doctrine, product/publication policies, handoff, campaign mission/plan, prior vault diagnosis and both ARB task prompts. Root MISSION.md is absent; the supplied campaign-root MISSION.md was read. Read `a34df04`, its freshness code and report. Its independent wire/public freshness separation is already represented in this integration; replaying it would add obsolete state. No cherry-pick was needed.

The shell has neither a private ARB clone nor GitHub login. The installed GitHub connector provided authorized read-only access. Canonical developments, main/checkpoint query exports and the recent candidate window were read at resolved immutable refs. No private files, identifiers, commit identities or logs were copied into the worktree. This report retains aggregate counts and public IDs only.

“After 09-18” means an event calendar date of September 19 or later. Directory/ID dates, discovery, recorded_at, verification, seal and edition times are separate; none is an event timestamp.

## Stage counts and losses

| Stage | Total input → output | Valid event_at after 09-18, in → out | Mechanism |
|---|---|---|---|
| Recent candidate window | 723 files → 2 linked canonical developments | 0 explicit event_at → 0; **2 alternate canonical event_date values** | 561 deferred, 27 investigating, 3 monitoring, 129 duplicates, 1 rejected, 2 accepted. Both accepted records link to the two undated developments. Candidate dates are intake dates. |
| All canonical developments / query projection | 46 → 46 | 0 → 0; **2 event_date values lost** | `build_query_index.py::normalize_record` emits only `event_at: r.get("event_at")`. Both new records have null event_at despite source-associated event_date and matching primary-source published_date. |
| Main / sealed checkpoint query | 46 / 46 | 0 / 0; 2 null dates in each | Observed query rows are identical between main and its named sealed checkpoint. Recent daily receipts do not introduce later event timestamps. |
| Compiler / airlock / bridge / guard | 46 → 46 sanitized records | 0 → 0; 2 null dates survive | Compiler inspection shows query rows pass through declassification/public-ID conversion/allowlists. Observed corpus contains all 46. No newer dated row is removed. Bridge safety/hash checks accept the null-date public objects; guard adds 0, misses 0 and records 3 withdrawals/merges. |
| Newsroom ingest | 46 → 41 publishable | 0 → 0 | 2 EVENT_AT_INVALID quarantines + 3 tombstoned IDs. Two invalid / 46 = 4.35%, below the existing 20% batch-refusal limit; valid historical content continues. No gate was relaxed. |
| A2 Story layer | 46 current rows + preserved history → 44 objects | 0 → 0 | Same two quarantines; 41 live, 1 withdrawn, 2 merged. Historical notices remain addressable. Front-page eligibility affects placement, not inclusion in stories.v2.json. |
| SSG / production data | 44 → 44 objects; 41 live / 123 localized Story routes | 0 → 0 | Actual local build preserves all Story IDs and bytes. Live JSON also has 44 objects and no later event. There is no extra build date cutoff. |

Compiler/bridge counts combine upstream code inspection and observed query/corpus endpoints. L21 did not execute the private compiler or retain private runner artifacts. Downstream ingest selection, Story construction and paper builds were executed locally.

Public identity: `newswire-a8ab11584169f896e64e2c0c`; digest `a8ab11584169f896e64e2c0cad5b7ed858319f648e97e6cf264c9eb635b03e3b`; airlock generated 2026-10-04T13:10:52.326373Z. Latest checked-in heartbeat: 03:03:38Z, CHECKPOINT / ARB_MAIN_RED. Its freshness does not repair the missing dates.

Quarantines:

- `FCMO-045BB8282222`, Argentina data-center power: canonical event_date **09-25**, query/corpus event_at **null**; recorded_at 2026-10-04T04:21:45.527006Z.
- `FCMO-5B5B447325A8`, OpenAI / Synopsys: canonical event_date **09-30**, query/corpus event_at **null**; recorded_at 2026-10-04T04:14:37.057940Z.

Other ingest exclusions: `FCMO-FDBE3D996243` (UNVERIFIED_RELEASE withdrawal), `FCMO-EEF757F0D806` and `FCMO-1E497EDC718A` (DUPLICATE tombstones). The September 18 event belongs to the **withdrawn** record. The newest **live** Story event is **2026-09-11T17:55:45Z**. The old editorial health command understated actual live-news age by reading the raw corpus.

533 deferred candidates explicitly belong to an intake pass where evidence was not fully inspected. There are 693 candidate files in the October 4 intake window; that is activity, not 693 current publication-ready stories. No directory date was promoted to an event date here.

## Workflow evidence

Read-only metadata confirms successful transport and refresh despite stale content:

- [Bridge 37236038973](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37236038973), 10-04 21:25Z, and [refresh 37236112674](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37236112674), 21:26Z: success, inside the operator-reported green-main interval.
- [Bridge 37257787277](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37257787277), 10-05 03:02Z: success; public wire status then reports ARB_MAIN_RED.
- [Refresh 37257787267](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37257787267): success, **status-only** path. [Chained refresh 37257863909](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37257863909) also succeeds. Status-only work creates no stories.
- [Pages 37258642854](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37258642854), starting 03:14Z: build, deploy, exact origin verification and LKG promotion all succeeded.
- [Health 37258914871](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37258914871): serving/editorial/publication failed; translation passed, independently of Pages success.

The complete 19:06–00:06 green-main interval is supplied operator evidence, not a private integrity history independently reconstructed here. The date-loss mechanism is proven independently of that interval. The 10-03 and 10-04 daily receipts were read and declare publication; they do not certify event freshness.

## Controlled causal test

Copied only the already-sanitized corpus into ignored `_audit/l21/counterfactual/`, set the two event_at fields to the canonical day representations, and built Story plus paper output. Production corpus and checked-in Story data remain unchanged.

Result: **46 objects / 43 live / 2 events after 09-18 / 129 localized Story routes**. Both records are front-page eligible and retain NATIVE_ARB ES/ZH. Both IDs appear in all three daily fronts. **13/13 gates pass**. This falsifies a hidden September 18 Story/build cutoff. It is an experiment, not an unsigned release repair or current-news proof. September 30 material is still stale on October 5.

## Local fixes

Implementation `fe81d0b`, after red-first commits `8c821fe`, `e60ebf6`, `223e1b4`:

- Serving health uses `--paper`, current SSG routes and v2 deployment identity. Shared Pages polling proves critical hashes; receipt validation rejects missing routes/forged candidate hashes. A correctly served LKG is independent of newer unpublished checkout status. An expected deployment artifact still pins a specific candidate. Legacy callers remain supported.
- Required browser health now uses `verificar_live_surfaces.py --paper`: EN/ES/ZH × root, daily front and lead article; checks rendered language, headline, lead/link and publication state. Old Signal Field/hash-route assertions are replaced with current assertions; the browser gate is retained.
- Editorial health reads live v2 Stories; withdrawn, merged, quarantined and future events cannot make it green. With Story input, it never falls back to an upstream timestamp. The signal includes the measured timestamp.
- Regenerated READY_TO_PUBLISH.md, which described TRANSPORT_DOWN and stale hashes although source status was DELAYED. Its verification gate was red before regeneration and green after. No gate was bypassed.

No event, source prose, locale pack, tombstone, seal, corpus digest or evidence label was patched to manufacture fresher news.

## Serving failure was persistent, not transient

The original local command reproduced **UNREACHABLE: production root does not identify the publication**. Production is HTTP 200 with `<title>FCMO</title>`, lacking the retired literal `FCMO AI Newsletter`. The old checker also uses retired route/build-manifest contracts.

The corrected command against the **same live URL** returned:

```text
SERVING OK release=newswire-a8ab11584169f896e64e2c0c stories=41 identity=exact candidate=a00d697912d0ef08a392d51872243ba8d020d4e4935d883087578280ec9d830d
```

**21 routes answer 200; 9 critical files match the served identity.** Public source_commit `ab3d123e4e6a01352b1b308e4bc7c5f85c2be9d2` matches the successful Pages run: v4 merged at `3f293f2` plus later status commits. Hourly health proves consistency with the served receipt; independent candidate-promotion proof remains Pages' expected-artifact oracle. Those boundaries are distinct.

Corrected editorial health remains EVENT_STALE, now measuring September 11 live news. Serving success does not claim freshness. A separate HTTP/source adapter passed the new nine-page assertions against live HTML; it is **not browser-rendering proof**.

## Validation / continuation

- Full suite, **no skip override**: **601 tests / 119.187s / 0 failures or errors / 3 skips**. Existing browser-dependent tests skip because this box lacks Playwright/Chromium. An intermediate overly broad receipt validation broke three email-fixture checks; this was corrected before the final full run.
- Final focused regressions/compatibility: **33 pass**. Initial red evidence covered unsupported paper mode, retired workflow contract, absent paper-browser contract and unavailable-record editorial freshness.
- Actual build: **510 routes / 41 live / 123 Story routes; 13/13 gates**. Counterfactual: **43 live / 129 Story routes; 13/13 gates**.
- `verify_release.py`: **7/7** after receipt regeneration; `build_ready_receipt.py --check`: pass; **46 contract fixtures** pass; compile and diff checks pass.
- Real browser command attempted: **no supported Chrome/Chromium/Edge installed**. No browser download/installation was performed. Claude must run the preserved browser gate on the host before merge.

Exact upstream engineering/prompt changes: [CR-L21-upstream.md](CR-L21-upstream.md). Two-date repair alone still misses the 36-hour SLO. Current/previous-day research, legitimate promotion, seal advancement and repeated unattended production proof remain required. L20's main repair is separate. No deployment or automatic fresh publication was performed here.

Host commands:

```sh
python3 -m unittest discover -s tests -v
python3 tests/harness/validate.py --all-fixtures
python3 tools/build_ready_receipt.py --check
python3 tools/verify_release.py
python3 -m tools.paper.build --stories site/data/stories.v2.json --status site/data/newsroom-status.json --out _audit/l21/host --base /FCMO-AI-Newsletter/
python3 tools/gates/run_all.py _audit/l21/host
python3 tools/verify_live_newsroom.py --serving-only --paper --identity-timeout-s 300
python3 tests/oraculos/verificar_live_surfaces.py --paper
python3 tools/editorial_freshness.py check --stories site/data/stories.v2.json
```

Last command should remain red until legitimate current news arrives. For recounting, run `publishable_rows` on corpus JSONL and `StoryInputs` / `build_stories`; compare the built Story ID set and Story route count. Count dates beyond the cutoff and nulls separately. Local public logs/experiments live in ignored `_audit/l21/`. The launcher supplied no external writable reports directory; this report is committed under this worktree's `reports/REPORT-L21.md`, with root pointers.

Resumen: ARB pierde las fechas de dos noticias antes del puente; la mayoría de candidatos sigue sin promover. Corregí serving y frescura de Newsletter y probé serving real. Suite y compuertas pasan; faltan navegador en host, reparación upstream y noticias actuales. Sin push.
