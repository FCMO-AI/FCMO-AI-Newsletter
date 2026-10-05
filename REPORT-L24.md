# L24 — Repair editorial admission and prove freshness

## Result and boundary

Local editorial health is **GREEN**. The real downstream bridge accepted today's sealed MAIN artifact, the rebuilt edition contains `FCMO-853344D6403E` with its unchanged event date `2026-10-05T00:00:00Z`, and the normal health computation measured **23.1 h** against the unchanged **36 h** limit. The locally served candidate also passed serving verification and composed overall health **GREEN**.

This is local proof, not a claim that production has been repaired. No push, GitHub dispatch, production deployment, email delivery, or issue closure was performed here. Production needs the steps below and its own post-deploy verification.

## Cause

The initial [issue #54](https://github.com/FCMO-AI/FCMO-AI-Newsletter/issues/54) reported 565.8 h at 07:44 UTC. By this checkout's baseline, the upstream date repairs had already admitted the September 25 and September 30 stories, reducing the observed newest-live-event age to 143.0 h. That resolved part of the older incident but still left editorial red.

Today's bridge had already delivered 49 sanitized records. Its receipt at `2026-10-05T22:37:44Z` says `transport=OK`, `source_mode=MAIN`, `arb_main=GREEN`, release `newswire-e4147cb906a8e17ee13e2070`. The [successful bridge run](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37383483371) and the independently verified release support that boundary.

The latest story's event date was present and correct in `corpus/data/developments.jsonl`. The rejection happened afterward: `tools/taxonomy.py` had no mapping for **`credible_unconfirmed`**, a valid canonical ARB confidence value. Story generation printed:

```text
QUARANTINE FCMO-853344D6403E CONFIDENCE_UNKNOWN
QUARANTINE FCMO-A2E27CF321FE CONFIDENCE_UNKNOWN
```

The second record concerns an October 1 research event. The health check correctly measures `event_at` only on live v2 Stories, excluding held and future records. It could not count the quarantined October 5 event. Neither the bridge nor the 36 h health policy required weakening.

## Fix

- Explicitly map `credible_unconfirmed` to the conservative Newsletter value `claimed_unverified`. Unknown confidence still quarantines. Evidence grades, claim labels, caveats, event dates, and date precision remain intact.
- Add a frozen, sanitized public-record regression fixture and red-first tests for every canonical ARB confidence value, Story admission, unchanged day-precision event dating, GREEN health today, and stale health after the actual event ages out. Both new tests failed before the mapping; both pass afterward.
- Add EN/ES/ZH labels for incoming confidence, blocked gaps, Brazil, and Portuguese source language so the new records also satisfy the existing reader-copy contract.
- Regenerate the newsroom with the repository tools: public briefs, imported native editions, source checks, media, Story layers, citations, locale receipts, newsroom ACK, frozen overlay, and release receipt. Freeze three newly published IDs through `story_layer ledger`; existing frozen entries remain unchanged. Existing valid source-check/media receipts are retained; new or revised public dossiers were re-researched.
- Replace stale live-corpus count assertions with independent identity/route censuses. Preserve the historical ledger fixture exactly and keep outage/stale counterfactuals explicit, so a recovered newspaper does not fail tests that assumed production would remain old.

The resulting source layer has **49 Story objects: 46 live, 1 withdrawn, 2 merged**, **138 native Story routes**, and **558 total routes**. Both native editions have **46 complete Stories, 0 pending, 0 failed**. Today's story remains `claimed_unverified`, with native ARB prose in both locales, and leads all three Diario editions.

## Evidence

- Before correction: local editorial `EVENT_STALE`, newest live event `2026-09-30T00:00:00Z`, age 143.0 h.
- Real bridge replay: `wire_status sealed-view` extracted the exact sealed bytes from today's transported corpus, excluding newsroom-owned files; the production partial-locale verifier/stager accepted the content-addressed release and corpus guard. The staged record and ES/ZH files are byte-identical to the inputs used by the newsroom rebuild. The isolated private ARB checkout/seal was not rerun locally; that upstream step is evidenced by the successful MAIN bridge delivery above.
- After correction: `EDITORIAL OK`, newest live event `2026-10-05T00:00:00Z`, age 23.1 h, limit 36 h. `HEALTH GREEN edition=FRESH red=-` when composed with the real serving check against the local candidate.
- `python3 -m unittest discover -s tests -v`: **606 tests, OK (3 existing conditional skips)**. Stateful refresh oracles were enabled.
- `python3 -m compileall -q tools tests`: passed.
- `python3 tools/verify_release.py`: **7/7 gates** passed, including frozen overlay and receipt agreement.
- `python3 tools/gates/run_all.py /tmp/l24-proof/publish`: **13/13 gates** passed. Existing upstream glossary warnings remain warnings; no gate was changed.
- Pinned Playwright 1.63.0 / Chromium: paper oracle passed **3 locales × 2 viewports**; layout checks covered 138 Story routes, 3 home pages, and 186 Chinese heading pages at both widths. Final browser/DOM inspection confirmed today's lead and `current` freshness in EN/ES/ZH.
- Real local HTTP serving check: all **21 critical routes** returned 200 and **9 critical file hashes** matched the candidate identity.
- `translation_health.py --all-corpus`: **HEALTHY**, ES/ZH backlog 0.
- Story and health JSON schema validation: passed. `git diff --check`: clean.

Local proof files are under `/tmp/l24-proof/`: `publish/`, `editorial.json`, `serving.json`, `health-state.json`, and `diario-en.png`. Test transcripts are `/tmp/l24-acceptance-tests.log`, `/tmp/l24-release-gates.log`, and `/tmp/l24-paper-oracle2.log`; these temporary files are not publication authority.

## Architect: push and production continuation

From the host Newsletter checkout, reconcile against the latest main before promotion. Do not force-push; if new corpus input arrived, rebuild the generated artifacts from that input before pushing. The repair branch is `repair/event-stale`.

```sh
git switch repair/event-stale
git fetch origin
git rebase origin/main
python3 -m unittest discover -s tests -v
python3 tools/build_final_release.py --check
python3 tools/build_ready_receipt.py --check
git diff --check
git push origin HEAD:main
```

If branch protection requires a PR, push `repair/event-stale` and merge it through the normal reviewed path instead. Then dispatch the normal bridge so it fetches and seals current ARB main with the read-only App:

```sh
gh workflow run newswire-bridge.yml --repo FCMO-AI/FCMO-AI-Newsletter --ref main
gh run list --repo FCMO-AI/FCMO-AI-Newsletter --limit 20
```

Wait for the successful bridge → autonomous refresh → Pages chain. The tooling change participates in the builder digest, so it forces a rebuild even if the Airlock digest is unchanged. If the automatic refresh is absent, dispatch it and wait for success:

```sh
gh workflow run daily-refresh.yml --repo FCMO-AI/FCMO-AI-Newsletter --ref main
```

If Pages does not chain, dispatch the production deploy and wait for build, deploy, public-origin verification, and LKG promotion:

```sh
gh workflow run pages.yml --repo FCMO-AI/FCMO-AI-Newsletter --ref main -f operation=deploy
```

Only after production verification, dispatch the production health computation:

```sh
gh workflow run newsroom-health.yml --repo FCMO-AI/FCMO-AI-Newsletter --ref main
gh run list --repo FCMO-AI/FCMO-AI-Newsletter --limit 20
```

Confirm today's Story/event in the live EN/ES/ZH Diario and `data/stories.v2.json`, editorial GREEN in the health artifact, and the automated alert transition/closure of #54. Do not close the incident based only on this local result. Freshness remains event-based: October 5's event naturally expires after 36 h; later research must supply later legitimate events.

The [latest skipped Diario dispatch](https://github.com/FCMO-AI/FCMO-AI-Newsletter/actions/runs/37384550861) skipped its entire job before any steps. `dispatch-email.yml` requires `FCMO_EMAIL_ENABLED=true` and, for a deploy-triggered run, a successful parent deploy. This is a separate activation control, not an editorial-date filter. Verify the flag and existing email environment prerequisites on GitHub; this repair does not enable or send email. Once delivery is intentionally enabled and the live LKG is verified, its regular deploy trigger or an explicit `dispatch-email.yml` dispatch owns delivery.
