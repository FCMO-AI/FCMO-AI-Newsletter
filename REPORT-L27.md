# L27 round 2 — Kit forms + Brevo v3

**Local implementation for review on `c5/email-kit`; no push, external network, provider account changes or real email.** The four adapters `kit`, `brevo`, `listmonk`, `fake` share the unchanged provider contract. L26's gateway, consent journal, SES, installation and host backup remain in place. Production activation, live API shapes/free-plan access and repeated autonomous delivery remain unproved.

Kit now defaults to **form membership**, removing the dependency on three form→tag Rules. `KIT_FILTER_MODE=form` (also the unset/empty default) requires only three distinct `KIT_FORM_EN/ES/ZH` IDs. Sending uses a form filter, health checks forms, backup derives locales from form membership. `KIT_FILTER_MODE=tag` explicitly retains optional tags and their verified assignment. The reported one-automation free-plan limit is the reason to remove the dependency; the account/plan was not inspected here.

Brevo uses three locale lists and three hosted **double opt-in** forms, contacts export, campaign create + `sendNow` through API v3. Its campaign `name` and `tag` carry the edition/locale key. Sending rereads the campaign detail and verifies locale selection and `queued`/`inProcess`/`sent` state. A draft does not prove scheduling. The assumed free allowance is the operator-supplied 300 emails/day across the account, with unlimited contacts; campaign API availability and actual quota behavior must be verified live before activation. No paid plan or credits were purchased.

## Configuration and activation

[EMAIL-PROVIDERS.md](docs/EMAIL-PROVIDERS.md) contains the configuration-only switch, public/private JSON formats, daily cap semantics and encrypted Kit→Brevo / Brevo→Kit migration procedure. The selector, generator and export contract do not require code changes to switch providers. Both provider notices are source-controlled in EN/es-419/zh-Hans; Brevo uses [email-privacy-brevo.json](legal/email-privacy-brevo.json). `FCMO_EMAIL_COMPLIANCE_READY` remains an activation gate, not evidence that the provider enforces consent.

Kit preparation:

1. Confirm the real Newsletter/free plan and v4 broadcast scheduling permission in the account. Create a **v4** API key (header `X-Kit-Api-Key`) and store it only as `KIT_API_KEY` in the `email` environment. No v3 secret or Bearer auth.
2. Create three forms, configure incentive/DOI in each language, keep auto-confirm off and verify the public embed action and email field. Set `KIT_FORM_EN/ES/ZH` as repository variables. **Do not create three automation Rules for default mode.** Leave `KIT_FILTER_MODE` unset or set `form`; leave production tags unused unless deliberately selecting `tag`.
3. Verify the sender `FCMO_EMAIL_FROM`, real postal address secret, body and one-click unsubscribe, suppressed states, disabled tracking, provider terms/transfer safeguards, effective retention and complete controller notice `FCMO_EMAIL_PRIVACY_URL`. Only then enable compliance. Prove that pending readers are excluded from the form-filtered broadcast and a confirmed seed receives only its chosen locale.
4. Existing Actions `test_mode` remains Kit-only: it explicitly overrides the filter to `tag`, selects `KIT_TEST_TAG_EN/ES/ZH` with no production fallback and checks each tag contains exactly `KIT_TEST_SUBSCRIBER_ID` active. Add the seed to these tags manually; no form→tag Rules are needed. Keep production forms unpromoted and audiences empty during preparation. Repeat a fresh test edition and require zero new broadcasts. Restore production form mode for the next edition date.

Brevo preparation:

1. Confirm the actual free plan, verified sender/domain and v3 campaign API entitlement; create a private v3 key. Create distinct DOI-confirmed locale lists. Store secret `FCMO_EMAIL_PROVIDER_CONFIG` as `{"api_key":"<private-key>","list_ids":{"en":<id>,"es-419":<id>,"zh-Hans":<id>}}`; only the IDs, not subscriber data, belong in configuration.
2. Create three hosted forms using Brevo DOI; only after confirmation may a contact enter the matching sendable list. Set public `FCMO_EMAIL_PUBLIC_CONFIG` with `forms` mapping each locale to its exact HTTPS `*.sibforms.com/serve/<token>` action and set the complete notice URL. The static form posts `EMAIL` and browser consent directly; no server/API key of ours is exposed. Confirm required hidden fields/CAPTCHA/consent field shape from the real embed before collecting addresses. If it needs fields unsupported by this form contract, keep signup off and fix the adapter/presentation from evidence. Directly creating active contacts is not a DOI fallback.
3. Complete the same sender/privacy/retention/tracking/unsubscribe gates. Prove pending/suppressed exclusion and final MIME with `{{ unsubscribe }}` resolved. The Kit-specific seed namespace is rejected by Brevo. Start with only confirmed private seeds in all three configured lists before promotion, between edition dates; do not enable production-sized lists merely to try the API.
4. Verify account-wide budget including DOI and other campaigns. Health sums the three lists' `totalSubscribers` and warns above 300 (`brevo_daily_cap_exceeded`). A subscriber in three locales needs three emails; 101×3 exceeds the cap. For disjoint lists the sum of their sizes is used. Health's estimate is not remaining-credit evidence; additional sends may exhaust the account below this threshold. The provider enforces the cap; the adapter never buys credits or bypasses it. Prove all three campaigns complete within the budget before claiming daily automation.

All providers preserve `FCMO_EMAIL_ENABLED`: off disables sends/forms, while encrypted backups remain available. Pages must be regenerated after a switch so the form and privacy notice change together. Switch between edition dates after reconciling the previous provider; cross-provider journals cannot prove a campaign was not already sent. Never delete intents/campaigns or rename keys to force retry.

## Recovery and backup

Actions validates live LKG identity/hashes, today's CDMX edition after 07:30, new stories and complete native EN/ES/ZH before health or intents. It restores prior same-day attempts, uploads an intent before mutation and attempts each locale independently. This lane does not change those gates or introduce translation.

Kit has one scheduling POST; Brevo has separate create and sendNow POSTs. GETs have at most three attempts with 25 s timeouts and 1/2 s pauses; POSTs one. Both providers lock/fsync local intent state before mutation and reread provider state. Brevo checks `name`, `tag`, list selection and status from detail, rejecting duplicates or an uncertain draft. A lost send response can reconcile to queued without another sendNow. A lost create response yielding a draft blocks for reconciliation. A restored intent with no observed campaign blocks recreation. `QUEUED` does not prove delivery or inbox placement.

The daily export streams original contact/subscriber fields plus `locales` into age. Only `.age` reaches disk/artifacts; retention is 30 days, decryption identity stays outside GitHub. Brevo exports all contacts rather than only active/list contacts and preserves `emailBlacklisted`, raw `listIds`, DOI-related attributes and other returned fields. A false blacklist flag is **not** evidence of DOI. Kit exports all five subscription states with form/tag membership. Failed export/encryption leaves no artifact. Migration must preserve suppressions from both providers and separately demonstrate consent, pending exclusion and state equivalence. No generic importer or automatic reactivation is supplied.

## Every assumed Kit shape to confirm live

These are synthetic fixture assumptions, **not downloaded documentation or a real account recording**. [Kit v4 reference](https://developers.kit.com/api-reference/overview) is a continuation link, not evidence of browsing. Confirm all rows before enabling; if real shapes differ, update the adapter and fixtures without weakening locale/consent/release gates.

| Boundary | Exact assumption / live confirmation required |
| --- | --- |
| Plan/capabilities | Free plan actually permits v4 filtered broadcast scheduling, three DOI forms and the selected membership APIs; default form mode needs no Rules. Optional tag automation and test-tag membership are separate checks |
| Origin/auth | `https://api.kit.com/v4`; JSON; `X-Kit-Api-Key` v4; credentials never forwarded on redirect; IDs positive numeric integers |
| Public signup | POST urlencoded `https://app.kit.com/forms/<id>/subscriptions`, field `email_address`, optional submitted `consent=yes`; actual required fields, anti-spam controls and public action host verified from embed |
| DOI semantics | Incentive email confirms mailbox; auto-confirm off; pending `inactive` excluded from broadcast even when form membership exists; browser checkbox does not prove provider-side consent enforcement |
| Forms health | `GET /forms?per_page=100&after=<cursor>` → `forms` rows with numeric `id`, including all three configured forms |
| Default broadcast filter | `subscriber_filter={"all":[{"type":"form","ids":[<locale-form-id>]}]}` accepted, persisted and actually selecting **only confirmed** members of this form |
| Optional tag filter | Same shape with `type=tag`; health `GET /tags` → `tags` with IDs; three distinct tags truly assigned, plan permitting the assignment; no default dependency |
| Create/schedule | `POST /broadcasts` accepts `subject`, full-HTML `content`, exact `description=fcmo-diario:<date>:<locale>`, verified sender `email_address`, `public=false`, filtered selection, UTC `send_at`; response `{"broadcast":{...}}` includes numeric ID and matching scheduling/filter fields |
| Schedule timing | Current UTC timestamp, including slightly elapsed timestamp in flight, accepted as intended; returned `send_at` demonstrates scheduling; account/timezone/delivery behavior verified |
| Broadcast lookup | `GET /broadcasts` → `broadcasts`; each row includes persistent exact `description`, `id`, `send_at`, `public`, `subscriber_filter`, including after sending. If summaries omit fields, add detail reads in the adapter before activation |
| Cursor pagination everywhere | `pagination.has_next_page` strict boolean; `end_cursor` nonempty string when another page exists, string/null on final page; `per_page=100`, `after`; same pagination for forms, tags, broadcasts, subscribers and membership endpoints |
| Global subscriber states | `GET /subscribers?status=active|inactive|bounced|complained|cancelled` includes each intended state; rows have numeric `id`, `email_address`, `state`, `fields`, `created_at` and all available suppression/consent fields; no omitted states needed for safe backup |
| Default locale export | `GET /forms/<id>/subscribers` yields all membership states including pending/suppressed; original state retained and form ID genuinely maps to locale. If default is active-only, fix the adapter to query all states from live evidence before relying on export |
| Optional tag export/seed | `GET /tags/<id>/subscribers` includes all states; `?status=active` on form/tag memberships yields only active with `state=active`. Seed tag contains exactly the configured numeric subscriber ID; no production fallback |
| Final mail | Full HTML accepted without unintended layout; `{{ unsubscribe_url }}` resolved in href; alternate text, postal/footer, body unsubscribe, RFC 8058 headers, disabled tracking, bounce/complaint/cancelled suppression verified in actual received MIME |
| Consistency/errors | Exact marker survives creation/sending; GET pagination/list lookup eventually exposes created broadcast; 429/5xx/timeout behavior and permission errors understood. Absence after an uncertain POST is a reconciliation blocker, never authority to retry |

Form/tag membership may overlap: choosing several locales can mean several emails. Confirm whether the intended account UX removes other memberships; this implementation does not silently make a single-locale promise.

## Brevo shapes to confirm live

[Brevo v3 reference](https://developers.brevo.com/reference) is likewise an unvisited continuation link. Confirm base `https://api.brevo.com/v3`, `api-key` auth; public `sibforms.com` POST/`EMAIL` and any hidden/CAPTCHA/consent fields; DOI list-entry and recorded confirmation semantics; `GET /contacts/lists/<id>` with `id`/`totalSubscribers` and the count's meaning; `GET /contacts` with `contacts`, `count`, `limit=100`, offset pagination, all suppressed/pending contacts, numeric IDs, `email`, boolean `emailBlacklisted`, `listIds`, raw attributes/timestamps; `GET /emailCampaigns` with `campaigns`, `count`, same pagination and persistent exact name; `GET /emailCampaigns/<id>` detail `id`, `name`, `tag`, `status`, `recipients.lists=[id]` with any other selector fields empty; POST create payload and returned numeric `id`; single POST `sendNow` with empty JSON returning 204; immediate/eventual `queued`/`inProcess`/`sent` observations; free-plan campaign entitlement and shared 300/day enforcement; body and one-click unsubscribe, suppression, tracking disabled and final MIME. Name/tag uniqueness is not assumed. Pagination changing counts/repeated IDs/incomplete pages fails closed rather than silently exporting a partial audience.

## Evidence and continuation

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

## Resumen en español — ronda 2

Kit ya usa membresía de formulario por defecto en envío, health y backup: no depende de tres automatizaciones del plan gratuito. Los tags quedan opcionales y la prueba seed conserva sus tres tags privados asignados manualmente. Brevo queda implementado bajo el mismo contrato con listas por idioma, formularios DOI alojados, campañas v3, reconciliación conservadora y export cifrado. Health avisa cuando la suma de envíos por idioma supera 300/día; otros envíos y confirmaciones también consumen ese cupo. La documentación explica el cambio solo por configuración y la migración cifrada Kit↔Brevo sin reactivar bajas ni convertir pendientes en confirmados. No hubo push ni correo real. Faltan confirmar APIs/planes/formularios reales, inspección en navegador y varios ciclos autónomos con entrega comprobada antes de activar lectores.
