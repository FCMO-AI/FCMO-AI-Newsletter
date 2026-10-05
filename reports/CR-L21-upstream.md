# CR L21 — preserve event dates and deliver current research

Owner: ARB engineering / Research Engine; Javier owns the task-prompt update. Separate from L20's duplicate/integrity repair. L21 changed no ARB file or setting.

## Proven defect and requested repair

The two newly promoted canonical developments contain a source-associated `event_date`, `event_time_precision: "date"`, and `event_at: null`. Their primary-source `published_date` values match. ARB's `tools/build_query_index.py::normalize_record` projects only `r.get("event_at")` and omits the alternate date. Newsletter receives two null timestamps and correctly quarantines both.

| Public record | Existing canonical event_date | Required day-precision event_at |
|---|---|---|
| FCMO-045BB8282222 — Argentina AI data-center power requirements | 2026-09-25 | 2026-09-25T00:00:00Z |
| FCMO-5B5B447325A8 — OpenAI / Synopsys EDA partnership | 2026-09-30 | 2026-09-30T00:00:00Z |

These dates were read from canonical fields and source metadata, not inferred from IDs or URL strings. Verify the primary-source locators before applying the updates. Midnight here represents day precision, not a known event time; Newsletter already interprets that representation as day precision.

1. Update these two canonical records through ARB's validated ingest/update path; retain their source locators and date precision. Rebuild query and public projections. Do not patch Newsletter's sealed corpus.
2. Define one canonical intake date contract: a valid, source-backed date-only `event_date` with `event_time_precision: "date"` must become canonical `event_at` before persistence. Reject conflicting date/timestamp pairs. A development claimed to be publication-ready must have a supported date; an unresolved candidate can remain in intake.
3. Preserve the canonical event timestamp in `build_query_index.py::normalize_record` and the sanitized field allowlists. Add a publication assertion that the supported canonical date survives query export and sanitized release. A seal must not silently discard a newly promoted development's only date representation.
4. Test the real chain: validated source-backed date-only input → canonical development → query projection → sanitized release. Cover both dates above, invalid/absent dates, conflicts and an old event recorded today. Never use recorded_at, last_verified_at, edition date, seal time or checkpoint time as event time.
5. Run ARB tests/doctor/ratchet and publication seal; advance PUBLICATION_READY through the established immutable-snapshot procedure only after success. Let the bridge receive the changed content-addressed release.

Downstream acceptance: 46 Story objects / 43 live / 1 withdrawn / 2 merged; both public IDs survive, with 129 localized Story routes. A controlled downstream experiment already demonstrated that shape and passed 13/13 gates. It is a counterfactual, not publication authority.

## Current-day supply is still required

The date repair yields September 30 material, still stale on October 5. A green main and new daily receipt do not replace current research. The recent intake window has 723 candidate files: 561 deferred, 27 investigating, 3 monitoring, 129 duplicates, 1 rejected and only 2 accepted/promoted.

Append this paragraph to task 1 and task 2's freshness section:

> Before historical catch-up or broad intake, cover the current and previous America/Mexico_City dates using dated primary sources. Inspect the strongest material recent items far enough to create source-backed canonical developments, with valid event_at, date precision, evidence labels and explicit gaps. A candidate file, scan count, daily brief or PUBLICATION.json is not proof that fresh material reached the public export. If material current news exists but none reaches the sealed public development projection, report the exact blocked stage and resolve it before expanding the backlog. Older deferred candidates remain useful depth work after current coverage. Never re-date old news or promote uninspected evidence to satisfy freshness.

Use the native ARB executor for rebuild, validation and sealing when the scheduled ChatGPT runtime cannot execute those tools. Record coverage gaps explicitly when no legitimate current item can be promoted. Do not accumulate noncanonical notes while claiming completed publication.

Completion still requires an unattended bridge → refresh → Story → gated build → Pages → live proof with legitimately current material and intact evidence, localization and historical publication dates. L21 establishes none of those upstream changes or a new deployment.
