# L27 — Kit tag sync + Brevo v3 and product naming

## Round-4 acceptance

Final full suite: **667 tests, OK, 3 existing skips**, on the implementation including sync-before-all-broadcasts. Focused email suite: **75 tests, OK**. Publication gates: **Kit 13/13, Brevo 13/13, retained L26 13/13**; agent hygiene passes for all three. Retained release verification: **7/7**. Evidence is in `reports/email-kit/round4-*`. The browser oracle returns `BROWSER_UNAVAILABLE`; generated signup structure was inspected for all three locales, but no new browser rendering or production delivery is asserted. The red-first commit is `14b2221`; `round4-sync-order-red.txt` also records the first-broadcast ordering regression.

## Current configuration — round 4

The email product, sender, and subscription are named **FCMO AI Newsletter** in EN, es-419, and zh-Hans signup copy, email headers and subjects, opt-in, privacy notices, community configuration, and workflow display names. The Spanish signup title is “Recibe la Newsletter de FCMO AI por correo.” Existing `diario` web routes and `fcmo-diario` technical idempotency markers remain unchanged. The reader-facing string regression is `tests/test_email_brand.py`.

**Local implementation for review on `c5/email-kit`; no push, external network, provider account changes or real email.** The four adapters `kit`, `brevo`, `listmonk`, `fake` share the unchanged provider contract. L26's gateway, consent journal, SES, installation and host backup remain in place. Production activation and repeated autonomous delivery remain unproved here. The operator supplied live Kit probe facts on 2026-10-05; the offline fixture now reproduces those boundaries.

Kit broadcasts use **tag filters only**, with the live response/payload list shape `[{"all":[{"type":"tag","ids":[N]}]}]`. Form filters returned 422 on the real free account. Before the first broadcast of each dispatch, the adapter paginates active subscribers of all three forms, posts `/tags/<tag>/subscribers/<id>` and confirms each subscriber's tags. Direct single-locale calls sync that locale before creation; the daily backup syncs all three forms before exporting. Missing tags are resolved/created by exact names `newsletter-en`, `newsletter-es-419`, `newsletter-zh-Hans`; optional `KIT_TAG_EN/ES/ZH` IDs override names. No Kit Rules are used. Explicit legacy `KIT_FILTER_MODE=form` is rejected.

The committed public defaults in `community/config/kit.json` are EN form 10007761 / uid 243b33b9e6, ES 10007787 / 65d33b22fa, ZH 10007798 / 2785dc2091. `KIT_FORM_*` and `KIT_FORM_UID_*` repository variables override them; empty Actions values use defaults. The unused embed form 10007671 is excluded. Static signup posts `email_address` to `https://app.kit.com/forms/<id>/subscriptions` and includes the corresponding hosted `https://fcmo-ai.kit.com/<uid>` link inside `<noscript>`. Build configuration contains no key.

`GET /tags/<id>/subscribers` lagged for minutes in the operator's probe; sync, seed checks and exports never use it. Exports query all five global and form states, then add per-subscriber tag memberships without dropping suppressions. Production sync only adds active form members and never reactivates anyone. It is additive: old tag assignments and overlapping locale choices can still produce several emails.

Brevo uses three locale lists and three hosted **double opt-in** forms, contacts export, campaign create + `sendNow` through API v3. Its campaign `name` and `tag` carry the edition/locale key. Sending rereads the campaign detail and verifies locale selection and `queued`/`inProcess`/`sent` state. A draft does not prove scheduling. The assumed free allowance is the operator-supplied 300 emails/day across the account, with unlimited contacts; campaign API availability and actual quota behavior must be verified live before activation. No paid plan or credits were purchased.

## Configuration and activation

[EMAIL-PROVIDERS.md](docs/EMAIL-PROVIDERS.md) contains the configuration-only switch, public/private JSON formats, daily cap semantics and encrypted Kit→Brevo / Brevo→Kit migration procedure. The selector, generator and export contract do not require code changes to switch providers. Both provider notices are source-controlled in EN/es-419/zh-Hans; Brevo uses [email-privacy-brevo.json](legal/email-privacy-brevo.json). `FCMO_EMAIL_COMPLIANCE_READY` remains an activation gate, not evidence that the provider enforces consent.

Kit preparation:

1. Keep the v4 key in the **repository secret** `KIT_API_KEY` (header `X-Kit-Api-Key`). Dispatch and backup have no `email` environment dependency. The operator reports successful free-plan tag-filtered creation and a scheduled broadcast delivered to their inbox; this session makes no external calls.
2. Use the committed locale forms/hosted links or override their IDs and uids together. Configure incentive/DOI, auto-confirm off, and verify real pending→confirmed→unsubscribe behavior. Production tags are created/resolved and filled through API sync; **no Rules** are required.
3. Verify `FCMO_EMAIL_FROM`, postal address secret, one-click unsubscribe, suppression, tracking, retention, terms and `FCMO_EMAIL_PRIVACY_URL` before enabling compliance. The live probe establishes API acceptance/delivery, not the whole consent/legal/MIME boundary.
4. Actions `test_mode` uses only explicit `KIT_TEST_TAG_EN/ES/ZH`, no production fallback, and a separate `fcmo-diario-test` key. Assign these seed tags manually. For a conservative seed isolation check, the **entire active account must contain only `KIT_TEST_SUBSCRIBER_ID`**, whose per-subscriber tags must include all three seed tags. It never syncs public forms into seed tags. Once other active readers exist, this seed mode fails closed; use a separately authorized proof instead of weakening the isolation check. Repeat the same edition to prove zero new broadcasts.

Brevo preparation:

1. Confirm the actual free plan, verified sender/domain and v3 campaign API entitlement; create a private v3 key. Create distinct DOI-confirmed locale lists. Store secret `FCMO_EMAIL_PROVIDER_CONFIG` as `{"api_key":"<private-key>","list_ids":{"en":<id>,"es-419":<id>,"zh-Hans":<id>}}`; only the IDs, not subscriber data, belong in configuration.
2. Create three hosted forms using Brevo DOI; only after confirmation may a contact enter the matching sendable list. Set public `FCMO_EMAIL_PUBLIC_CONFIG` with `forms` mapping each locale to its exact HTTPS `*.sibforms.com/serve/<token>` action and set the complete notice URL. The static form posts `EMAIL` and browser consent directly; no server/API key of ours is exposed. Confirm required hidden fields/CAPTCHA/consent field shape from the real embed before collecting addresses. If it needs fields unsupported by this form contract, keep signup off and fix the adapter/presentation from evidence. Directly creating active contacts is not a DOI fallback.
3. Complete the same sender/privacy/retention/tracking/unsubscribe gates. Prove pending/suppressed exclusion and final MIME with `{{ unsubscribe }}` resolved. The Kit-specific seed namespace is rejected by Brevo. Start with only confirmed private seeds in all three configured lists before promotion, between edition dates; do not enable production-sized lists merely to try the API.
4. Verify account-wide budget including DOI and other campaigns. Health sums the three lists' `totalSubscribers` and warns above 300 (`brevo_daily_cap_exceeded`). A subscriber in three locales needs three emails; 101×3 exceeds the cap. For disjoint lists the sum of their sizes is used. Health's estimate is not remaining-credit evidence; additional sends may exhaust the account below this threshold. The provider enforces the cap; the adapter never buys credits or bypasses it. Prove all three campaigns complete within the budget before claiming daily automation.

All providers preserve `FCMO_EMAIL_ENABLED`: off disables sends/forms, while encrypted backups remain available. Pages must be regenerated after a switch so the form and privacy notice change together. Switch between edition dates after reconciling the previous provider; cross-provider journals cannot prove a campaign was not already sent. Never delete intents/campaigns or rename keys to force retry.

## Recovery and backup

Actions validates live LKG identity/hashes, today's CDMX edition after 07:30, new stories and complete native EN/ES/ZH before health or intents. It restores prior same-day attempts, uploads an intent before mutation and attempts each locale independently. This lane does not change those gates or introduce translation.

Kit has one scheduling POST; Brevo has separate create and sendNow POSTs. GETs have at most three attempts with 25 s timeouts and 1/2 s pauses; POSTs one. Both providers lock/fsync local intent state before mutation and reread provider state. Brevo checks `name`, `tag`, list selection and status from detail, rejecting duplicates or an uncertain draft. A lost send response can reconcile to queued without another sendNow. A lost create response yielding a draft blocks for reconciliation. A restored intent with no observed campaign blocks recreation. `QUEUED` does not prove delivery or inbox placement.

The daily export streams original contact/subscriber fields plus `locales` into age. Only `.age` reaches disk/artifacts; retention is 30 days, decryption identity stays outside GitHub. Brevo exports all contacts rather than only active/list contacts and preserves `emailBlacklisted`, raw `listIds`, DOI-related attributes and other returned fields. A false blacklist flag is **not** evidence of DOI. Kit syncs active forms and exports all five subscription states with form and per-subscriber tag membership. Failed export/encryption leaves no artifact. Migration must preserve suppressions from both providers and separately demonstrate consent, pending exclusion and state equivalence. No generic importer or automatic reactivation is supplied.

## Kit evidence boundaries and remaining live checks

The fixture includes operator-reported 2026-10-05 probe facts (free plan, form-filter 422, tag-filter list, idempotent tag membership, lagging tag listing, hosted forms and scheduled delivery). Remaining rows still require account verification; the fixture is not a recording. [Kit v4 reference](https://developers.kit.com/api-reference/overview) is a continuation link, not evidence of browsing. Confirm all rows before enabling; if real shapes differ, update the adapter and fixtures without weakening locale/consent/release gates.

| Boundary | Exact assumption / live confirmation required |
| --- | --- |
| Plan/capabilities | Operator reports free plan accepts tag-filtered scheduled broadcasts and delivery; one automation only. No Rules used |
| Origin/auth | `https://api.kit.com/v4`; JSON; `X-Kit-Api-Key` v4; credentials never forwarded on redirect; IDs positive numeric integers |
| Public signup | POST urlencoded `https://app.kit.com/forms/<id>/subscriptions`, field `email_address`, optional submitted `consent=yes`; actual required fields, anti-spam controls and public action host verified from embed |
| DOI semantics | Incentive email confirms mailbox; auto-confirm off; pending `inactive` excluded from broadcast even when form membership exists; browser checkbox does not prove provider-side consent enforcement |
| Forms health | `GET /forms?per_page=100&after=<cursor>` → `forms` rows with numeric `id`, including all three configured forms |
| Broadcast filter | Operator observed form filter 422; tag filter accepted. Exact shape `[{"all":[{"type":"tag","ids":[<locale-tag-id>]}]}]`; form filtering stays available only in contracts for providers that support it |
| Active sync | Paginated `GET /forms/<id>/subscribers?status=active`, then `POST /tags/<tag>/subscribers/<id>` (201 first, 200 repeated), verify `GET /subscribers/<id>/tags`; tag-by-name creation shape still to confirm live |
| Create/schedule | `POST /broadcasts` accepts `subject`, full-HTML `content`, exact `description=fcmo-diario:<date>:<locale>`, verified sender `email_address`, `public=false`, filtered selection, UTC `send_at`; response `{"broadcast":{...}}` includes numeric ID and matching scheduling/filter fields |
| Schedule timing | Current UTC timestamp, including slightly elapsed timestamp in flight, accepted as intended; returned `send_at` demonstrates scheduling; account/timezone/delivery behavior verified |
| Broadcast lookup | `GET /broadcasts` → `broadcasts`; each row includes persistent exact `description`, `id`, `send_at`, `public`, `subscriber_filter`, including after sending. If summaries omit fields, add detail reads in the adapter before activation |
| Cursor pagination everywhere | `pagination.has_next_page` strict boolean; `end_cursor` nonempty string when another page exists, string/null on final page; `per_page=100`, `after`; same pagination for forms, tags, broadcasts, subscribers and membership endpoints |
| Global subscriber states | `GET /subscribers?status=active|inactive|bounced|complained|cancelled` includes each intended state; rows have numeric `id`, `email_address`, `state`, `fields`, `created_at` and all available suppression/consent fields; no omitted states needed for safe backup |
| Locale export | Query forms explicitly for all five states, add tags from each subscriber; preserve raw suppression state and locale intent |
| Seed isolation | Account-wide active list contains only the configured seed, with all three seed tags from per-subscriber lookup. Never rely on lagging tag subscriber listing |
| Final mail | Full HTML accepted without unintended layout; `{{ unsubscribe_url }}` resolved in href; alternate text, postal/footer, body unsubscribe, RFC 8058 headers, disabled tracking, bounce/complaint/cancelled suppression verified in actual received MIME |
| Consistency/errors | Exact marker survives creation/sending; GET pagination/list lookup eventually exposes created broadcast; 429/5xx/timeout behavior and permission errors understood. Absence after an uncertain POST is a reconciliation blocker, never authority to retry |

Form/tag membership may overlap: choosing several locales can mean several emails. Confirm whether the intended account UX removes other memberships; this implementation does not silently make a single-locale promise.

## Brevo shapes to confirm live

[Brevo v3 reference](https://developers.brevo.com/reference) is likewise an unvisited continuation link. Confirm base `https://api.brevo.com/v3`, `api-key` auth; public `sibforms.com` POST/`EMAIL` and any hidden/CAPTCHA/consent fields; DOI list-entry and recorded confirmation semantics; `GET /contacts/lists/<id>` with `id`/`totalSubscribers` and the count's meaning; `GET /contacts` with `contacts`, `count`, `limit=100`, offset pagination, all suppressed/pending contacts, numeric IDs, `email`, boolean `emailBlacklisted`, `listIds`, raw attributes/timestamps; `GET /emailCampaigns` with `campaigns`, `count`, same pagination and persistent exact name; `GET /emailCampaigns/<id>` detail `id`, `name`, `tag`, `status`, `recipients.lists=[id]` with any other selector fields empty; POST create payload and returned numeric `id`; single POST `sendNow` with empty JSON returning 204; immediate/eventual `queued`/`inProcess`/`sent` observations; free-plan campaign entitlement and shared 300/day enforcement; body and one-click unsubscribe, suppression, tracking disabled and final MIME. Name/tag uniqueness is not assumed. Pagination changing counts/repeated IDs/incomplete pages fails closed rather than silently exporting a partial audience.

## Historical round-2 evidence and continuation

Round-2 red-first contracts are committed as `9742139`; initial failures were absent Brevo and Kit tag-only filtering. [round2-red-first.txt](reports/email-kit/round2-red-first.txt) records the completed red run (78 tests, including an initial duplicated discovery of the imported contract class, 5 failures/14 errors). Discovery was corrected to import the test module rather than exposing its class twice. [round2-warning-red.txt](reports/email-kit/round2-warning-red.txt) additionally proves the provider-independent health-warning gap before its fix. Published logs normalize machine paths. The initial publication scan correctly rejected raw traceback paths; sanitized logs pass the same unchanged gate.

**Final acceptance:** email **67/67**; full suite **659 tests, OK, 3 skips** in 144.939 s; Kit and Brevo generated publications **13/13 gates each**; retained release verification **7/7**; agent hygiene **PASS** for both candidates; rendered form/privacy structure **6/6**; workflow YAML, preview Node syntax and `git diff --check` **PASS**. The three skips are the historical skip and two browser-dependent tests. The [initial full run](reports/email-kit/round2-initial-full-tests.txt) failed seven gate tests because saved red tracebacks still contained machine paths; normalization fixed the evidence files without changing or bypassing the gate, and the final full run passes. Evidence lives in [reports/email-kit/](reports/email-kit/). Prior-round evidence (52 email tests, 644 full tests, 13 publication gates, 7 release gates) remains in that directory as historical evidence. This round does not claim a new native Listmonk/Postgres run: that binary is still unavailable. Browser oracle was attempted and returned `BROWSER_UNAVAILABLE`; no dependencies were downloaded and no visual approval was asserted.

Reproduction:

```sh
python3 -m unittest discover -s tests -p 'test_email*py'
python3 -m unittest discover -s tests
python3 tools/verify_release.py
# Build each provider with synthetic public configuration; no key needed:
FCMO_EMAIL_PROVIDER=kit FCMO_EMAIL_ENABLED=true FCMO_EMAIL_COMPLIANCE_READY=true \
  KIT_FORM_EN=101 KIT_FORM_ES=102 KIT_FORM_ZH=103 \
  FCMO_EMAIL_PRIVACY_URL=https://example.org/complete-notice \
  python3 tools/paper/build.py --stories site/data/stories.v2.json \
  --status site/data/newsroom-status.json --out /tmp/l27-proof --base /FCMO-AI-Newsletter/
cp i18n/glossary.yml /tmp/l27-proof/data/glossary.json
python3 tools/gates/run_all.py /tmp/l27-proof
python3 tools/validate_agent_hygiene.py --site /tmp/l27-proof
# Repeat with brevo and the public forms JSON documented in EMAIL-PROVIDERS.md.
# With an already-installed browser, repeat the oracle and review screenshots:
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  python3 tests/oraculos/verificar_paper.py /tmp/l27-proof
FCMO_EMAIL_PROVIDER=kit KIT_FORM_EN=101 KIT_FORM_ES=102 KIT_FORM_ZH=103 \
  PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  node ops/email/review_preview.cjs reports/email-preview /tmp/l27-proof
# The preview inspector also accepts brevo plus FCMO_EMAIL_PUBLIC_CONFIG.
```

Claude must rerun final checks/browser inspection outside this box before integration, confirm provider shapes/free-plan permission privately, test real pending→confirmed→unsubscribe/suppression and received MIME, prove encrypted restore and several consecutive unattended daily cycles. `FCMO_EMAIL_ENABLED=false` plus a Pages redeploy is rollback; already sent emails cannot be recalled. Preserve audience, suppressions, backups and intents.

## Resumen en español — ronda 4

Kit vuelve a filtros de tag con lista de filtros, sync API de los tres formularios activos antes del primer broadcast y durante el backup, sin Rules. La confirmación de tags se hace por suscriptor; el listado del tag no se usa porque el probe real mostró demora. Los IDs/uids reales están como defaults públicos con overrides de variables. El sitio publica un POST con `email_address` y un enlace alojado sin JavaScript. Los workflows leen `KIT_API_KEY` del repositorio sin depender del environment `email`. El probe del operador prueba aceptación/entrega en plan gratuito; esta sesión verifica el software local y no afirma entrega nueva ni producción continua.
