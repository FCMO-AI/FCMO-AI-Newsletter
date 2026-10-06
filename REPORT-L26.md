# L26 — FCMO AI Newsletter email

**Implemented and proved offline; production email is not activated and no reader was emailed. No push was performed.** The chosen route is Listmonk 6.2.0 + Amazon SES, with the evidence and alternative costs in [EMAIL-ROUTE.md](reports/EMAIL-ROUTE.md).

The actual public 2026-10-05 edition was rendered through the real Listmonk template engine and delivered to a loopback SMTP sink in EN/es-419/zh-Hans. HTML, plain text, screenshots and machine-readable receipts are in [reports/email-preview/](reports/email-preview/). The visible postal address and recipient URLs there are explicitly synthetic preview values; they cannot be used for production.

## What is ready

- Image digests are pinned in `ops/email/images.json`: Listmonk 6.2.0 and the PostgreSQL 17 image resolved on 2026-10-05. Database traffic stays on a private Podman network; Listmonk binds to host `127.0.0.1:9000`, and the Python gateway to `127.0.0.1:9010`. No MTA or database is exposed to the Internet.
- The workflow retains successful-deploy triggering, the two daily retry windows, public LKG identity and full critical-route verification. It now authenticates to the gateway using a separate dispatch capability; no delivery or subscriber-management key enters GitHub. The host independently rechecks the public LKG tag, live candidate, hashes and freshness before rendering.
- SQLite and an OS lock serialize per-edition/per-language campaign creation across processes and restarts. Lost acknowledgements reconcile against existing campaign names; absent or conflicting state blocks rather than recreating a campaign. Campaign start means `QUEUED`, not delivered or inbox placement.
- All three languages use the same selected canonical IDs and committed native prose. No email translation provider exists. An incomplete selected language stops the operation before any campaign is created. The former Spanish-only signup policy remains for the legacy Ghost path; this explicitly requested Diario path supports EN/ES/ZH and leaves Javier’s Letters separate.
- The real site form uses ordinary HTML POST, an unchecked required consent box, a language choice, a privacy link, a honeypot and server-side limits. Only public double-opt-in lists are permitted. The gateway stores short-lived keyed consent/rate hashes, not clear email/IP records; Listmonk holds the private audience. The public API and default signup form are not exposed, preventing a consent bypass.
- Every Diario has recipient-specific body opt-out, preferences, plaintext and RFC 8058 one-click headers. Confirmation mail also includes opt-out and, at installation, the runtime postal address. Tracking is disabled. Hard bounces/complaints blocklist after one event; repeated soft bounces after three. SES feedback requires both the configured SNS topic and Listmonk signature validation.
- Install, activate, rollback, daily encrypted backup and unconfirmed-subscription expiry are under `ops/email/`. Privacy copy is source-controlled and rendered for all three site locales. Rollback never deletes audience or dispatch state.

## Evidence

Red-first: `tests/test_email_listmonk.py` initially failed on the missing provider implementation; the preserved record is `reports/email-preview/red-first.txt`. Failure cases now cover missing live verification, incomplete locales, unsafe single-opt-in lists, duplicate campaigns, lost create/start acknowledgements, restart, content/template injection and signup consent/limits. Gateway tests independently cover authorization, changed LKG/candidate, foreign SNS topics and closed administrative paths.

The native integration uses the checksum-verified official Listmonk binary, temporary PostgreSQL 17, synthetic contacts and a loopback SMTP sink. It observes four confirmation messages, three confirmed-reader Diario messages, zero Diario messages to the unconfirmed reader, zero duplicate messages after dispatcher restart, three successful one-click unsubscribes, two bounce/complaint suppressions, and rejection of unsigned SNS input. The actual post-template MIME bodies are the preview files. A real PostgreSQL dump and SQLite snapshot were archived, age-encrypted, decrypted and inspected; all three dispatch records survived, expired consent was removed, and temporary cleartext files were cleaned up. The unavailable Podman execution boundary was replaced with native `pg_dump`, and retention API responses were faked for this backup check; actual maintenance API syntax was also checked against Listmonk. The integration found and fixed a settings-reload race and an unwanted default Listmonk wrapper; the raw HTML template now preserves the real locale document.

Browser inspection also found overlapping Chinese signup-heading text. The scoped heading spacing was corrected and the final email/signup surfaces were inspected at 390 and 1440 pixels. Browser receipts report twelve checks, no overflow, three article cards per email, correct default signup languages, unchecked required consent, privacy links and zero script errors. Chromium evidence is not proof of Outlook/Gmail client rendering or inbox placement.

Validation commands and results are recorded at the end of this report. No privacy, localization, copyright, release or browser gate was weakened.

## 1. Architect: host steps

1. Use a real login session on the Debian host as the service user. This execution environment has Podman but **no `/etc/subuid` or `/etc/subgid` allocations and no user-systemd bus**. `install.sh` therefore intentionally cannot complete here. A host administrator must allocate an unused, non-overlapping range of at least 65,536 subordinate UIDs/GIDs and ensure a persistent user manager. If `100000–165535` is free, the administrator’s commands are:

   ```sh
   sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 fcmo-agent
   sudo loginctl enable-linger fcmo-agent
   ```

   Do not reuse that range if another account already owns it. Re-login, run `podman system migrate` only with awareness of this user’s other containers, then prove `podman unshare cat /proc/self/uid_map` and `systemctl --user show-environment` work. This session has no root and did not perform these changes.

2. Ensure `podman`, `python3`, PostgreSQL-compatible tools inside the pinned database container, `age`, and public Caddy/TLS are available. Arrange a separately held age decryption key and put only its public recipient in `email.env`. The secrets directory must be writable by its legitimate administrator; do not substitute a committed `.env` or broaden its permissions.

3. After the operator has supplied the private environment file, run from this unpushed checkout (or a later reviewed host checkout):

   Leave the initial `LISTMONK_API_KEY` empty until step 4 creates it; installer validation explicitly allows that first-boot dependency. Activation requires the real key.

   ```sh
   ops/email/install.sh
   systemctl --user status fcmo-email-db fcmo-email-listmonk
   ```

   The script validates host support and the 0600 environment file before installing source-only snapshots into `~/.local/share/fcmo-email/releases/`. It creates a private network/volume, writes minimal database-only container env files, copies units, starts the database, performs an idempotent first install and starts Listmonk. It never configures public ingress or starts a newsletter.

4. Through an SSH/Tailscale tunnel to **127.0.0.1:9000**, create the initial Listmonk web administrator with a strong password and 2FA, then an API user/token. Keep all `/admin` and `/api` routes private. Use a bootstrap API role with list/template/settings maintenance permissions; the ongoing gateway requires list/template read, campaign read/manage and public subscription access. The API key remains on the host. Set `LISTMONK_API_USER` and `LISTMONK_API_KEY` in `email.env`, then:

   ```sh
   ops/email/activate.sh
   systemctl --user status fcmo-email-gateway fcmo-email-maintenance.timer
   systemctl --user start fcmo-email-maintenance.service
   ```

   Observe the encrypted `.tar.age` backup in `~/.local/share/fcmo-email/backups/`, verify decryption privately and verify the timer’s next run. There are no provider calls hidden in the build. Bootstrap configures SES SMTP with STARTTLS and certificate verification, lists, privacy, suppressions and the raw HTML template; it waits through Listmonk’s restart and re-reads settings/lists. It refuses transport changes while campaigns are running.

5. Replace the hostname in `ops/email/Caddyfile`, import that block into the existing HTTPS Caddy configuration, validate and reload it using the existing service owner’s mechanism. The block exposes only consent signup, authenticated dispatch, complete privacy notice, recipient confirmation/preferences/export/delete paths, their static assets and SES feedback. It intentionally denies `/subscription/form`, `/api`, `/admin`, campaign archives and tracking endpoints. It overrides `X-Real-IP` from the TCP peer. Avoid access logs containing recipient tokens or request bodies.

6. Before enabling GitHub dispatch, subscribe controlled Gmail, Outlook and Yahoo seed mailboxes in each committed language; confirm by clicking and submitting the confirmation page, inspect SPF/DKIM/DMARC and one-click headers, verify postal/contact copy, exercise unsubscribe and data export/delete, and use SES mailbox simulator feedback to prove the signed SNS path. Begin at the configured two messages/second; adjust only within the approved SES rate/quota and warm volume gradually. No seed mailboxes were supplied in this task, so these effects were not attempted.

7. For operational checks, inspect Listmonk campaign counts/states, SES delivery/bounce/complaint metrics, the workflow result, the backup timer and disk capacity. Provider acceptance and `finished` can include delivery failures; reconcile sent/failed counts and mailbox evidence. Several consecutive autonomous daily cycles remain required by `PRODUCT_GOAL.md`.

Rollback:

```sh
ops/email/rollback.sh
```

Also set GitHub `FCMO_EMAIL_ENABLED=false`, redeploy the form-disabled site and remove the email ingress block. The script restores the previous source snapshot when present, disables the gateway and preserves the database/journal. A first-install rollback stops the stack. It cannot recall delivered messages. Do not delete a campaign, rename a deterministic campaign or clear the journal to retry an edition.

For a database disaster, stop gateway/Listmonk, decrypt a backup into a private 0700 directory, restore PostgreSQL and SQLite together, and reconcile every potentially started campaign against surviving delivery evidence **before restarting sending**. An older backup is not permission to send an old edition again. No automatic destructive restore is included.

## 2. Operator: one-time account, credentials, DNS and exposure

1. Choose the sending domain and public email hostname. No actual domain or public IP was supplied, so production hostnames and account-specific DKIM selectors cannot truthfully be invented. The executable DNS step below emits the exact values once the real identity exists. The proposed region is **us-east-1**; use the same region for identity, SMTP, approval, feedback and DNS.

2. Create/enable an AWS account, arrange billing, select SES **à-la-carte** (or deliberately accept Essentials), request production access for an opt-in daily newsletter and sufficient quota for 10k daily messages plus confirmations/retries. Sandbox access is not production access. Verify the actual sending domain with Easy DKIM. Set custom MAIL FROM to `bounce.<SENDING_DOMAIN>` with **RejectMessage** on MX failure. Enable account-level hard-bounce/complaint suppression. [SES production access](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html), [custom MAIL FROM](https://docs.aws.amazon.com/ses/latest/dg/mail-from.html).

3. Create restricted, region-specific SES SMTP credentials. The chosen route uses **SMTP username/password**, not a Mailgun/Ghost REST API key. Put those plus the **Listmonk API token**, separate dispatch token, consent-hash key and database password into `/etc/fcmo/secrets/email.env`, using `ops/email/email.env.example` as the key catalogue. Generate random credentials with `openssl rand -hex 32`; never paste them in a report, issue, shell argument, screenshot or repository. Keep the file 0600 and host-private. No SMTP credential is needed in GitHub.

4. Supply a real editorial postal address and monitored privacy/ARCO/withdrawal contact. Arrange the AWS processor agreement and applicable international-transfer safeguards. Keep the shipping controller identity (Matías Peña Szőke) or update all three notice translations together if legal responsibility differs. Set `FCMO_EMAIL_COMPLIANCE_READY=true` only after these facts are real. This is an activation prerequisite, not a claim that software proves legal compliance.

5. Create an SNS topic in us-east-1 for SES bounce and complaint identity notifications, include original headers, and subscribe its HTTPS endpoint to `https://<EMAIL_HOST>/webhooks/service/ses`. Enable both identity feedback types; the gateway must have its exact ARN in `FCMO_EMAIL_SES_TOPIC_ARN`. SES/Listmonk recipient headers allow correlation. The gateway admits only that topic, and Listmonk verifies SNS signatures and handles subscription confirmation. Confirm the real topic subscription and test suppression before enabling sends. [SES feedback notifications](https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html), [Listmonk bounce handling](https://listmonk.app/docs/bounces/).

6. Fetch the SES identity response locally through the authenticated AWS console/CLI:

   ```sh
   aws sesv2 get-email-identity --region us-east-1 \
     --email-identity '<SENDING_DOMAIN>' > /private/ses-identity.json
   python3 ops/email/dns_records.py \
     --domain '<SENDING_DOMAIN>' --region us-east-1 \
     --identity-json /private/ses-identity.json \
     --email-host '<EMAIL_HOST>' --public-ip '<HOST_PUBLIC_IP>' \
     --out /private/email-dns.json
   ```

   The exact record data is:

   | DNS name | Type | Value |
   | --- | --- | --- |
   | `bounce.<SENDING_DOMAIN>` | TXT | `v=spf1 include:amazonses.com ~all` |
   | `bounce.<SENDING_DOMAIN>` | MX, priority 10 | `feedback-smtp.us-east-1.amazonses.com` |
   | `_dmarc.<SENDING_DOMAIN>` | TXT | `v=DMARC1; p=none; adkim=r; aspf=r; pct=100` |
   | each actual SES token + `._domainkey.<SENDING_DOMAIN>` | CNAME | that same actual token + `.dkim.amazonses.com` |
   | actual `<EMAIL_HOST>` | A or AAAA | actual reachable public host address |

   The generator requires three real Easy DKIM tokens and rejects absent/fabricated placeholder inputs. Publish exactly one SPF TXT and one MX for the dedicated MAIL FROM name; do not add a second SPF policy to an existing domain. DMARC starts at monitoring; after observing alignment and legitimate senders, tighten it deliberately. Account-generated selectors and the real hostname/IP are the only missing values, not hidden “magic DNS.” [AWS Easy DKIM](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html).

7. Expose the email hostname through existing Caddy on public 443 with valid TLS and reachable DNS. Private Tailscale access alone cannot serve public signup, mailbox confirmation/unsubscribe, GitHub-hosted dispatch or SNS callbacks. If public ingress is unavailable, a configured public tunnel/Funnel can expose the **restricted Caddy handler**, not unrestricted Listmonk; its stable HTTPS hostname becomes `FCMO_EMAIL_PUBLIC_URL`. Prove it from an external network. No public exposure was created by this task.

## 3. GitHub variables and secrets

Configure in the publication repository, using the existing `email` environment for the dispatch secret:

| Kind | Name | Exact role |
| --- | --- | --- |
| Repository variable | `FCMO_EMAIL_PUBLIC_URL` | Clean public HTTPS origin of restricted email service, no query, credentials or path. Used by Pages and dispatch. |
| Repository variable | `FCMO_EMAIL_ENABLED` | Keep `false` until host, domain, SES approval, feedback, privacy, backup and seed-mailbox proof are complete; then set to literal `true`. |
| `email` environment secret | `FCMO_EMAIL_DISPATCH_TOKEN` | Same random token as host `email.env`; only permission to request a verified Diario dispatch. |

`GHOST_URL`, `GHOST_ADMIN_API_KEY` and GitHub `FCMO_EMAIL_POSTAL_ADDRESS` are no longer required for this route. The actual postal address is host runtime data and is included in every email and complete notice. No audience records or provider keys belong in GitHub. Keep the email environment restricted to reviewed `main` runs; existing contents-read permission and workflow concurrency remain unchanged.

After eventual reviewed publication (outside this no-push task), set the public URL, deploy the repository while the enable flag is false, verify the service externally, then enable and manually run Pages to publish the real form. Wait for LKG promotion and run the dispatch workflow. The independent host recheck prevents a race with an unverified or changed candidate. A scheduled retry recovers a failed trigger but cannot bypass current-day eligibility or the durable journal.

## Reproduce the offline evidence

The test is offline with respect to delivery; acquiring software/browser binaries is a separate preparation step. Listmonk release tarball SHA-256 was compared with its official `listmonk_6.2.0_checksums.txt` before execution. [Official release](https://github.com/knadh/listmonk/releases/tag/v6.2.0).

```sh
python3 -m unittest discover -s tests -p 'test_email*py'
python3 ops/email/offline_e2e.py --listmonk /path/to/verified/listmonk \
  --pg-bin /usr/lib/postgresql/17/bin
FCMO_EMAIL_PUBLIC_URL=https://mail.example.org python3 tools/paper/build.py \
  --stories site/data/stories.v2.json --status site/data/newsroom-status.json \
  --out /tmp/l26-proof/publish --base /FCMO-AI-Newsletter/
cp i18n/glossary.yml /tmp/l26-proof/publish/data/glossary.json
python3 tools/gates/run_all.py /tmp/l26-proof/publish
python3 tools/validate_agent_hygiene.py --site /tmp/l26-proof/publish
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  node ops/email/review_preview.cjs reports/email-preview /tmp/l26-proof/publish
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  python3 tests/oraculos/verificar_paper.py /tmp/l26-proof/publish
python3 tools/build_ready_receipt.py
python3 tools/verify_release.py
PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
  python3 -m unittest discover -s tests
```

Final proof: focused email tests **34 passed**; full suite **626 tests run: 625 passed, one existing skip**, in 143.342 seconds; native stack and encrypted-backup proof **PASS**; publication gates **13/13**; release gates **7/7**; agent hygiene **PASS**; newspaper browser oracle **PASS**; email/signup browser proof **12/12**; Caddy configuration validation, Python compilation, shell syntax and `git diff --check` **PASS**. These results include the final visual correction and refreshed release receipt. Summaries are preserved in [acceptance.json](reports/email-preview/acceptance.json), with separate native, backup and browser receipts. Scratch services were stopped after verification. Rootless container/systemd installation could not be exercised in this session because its host prerequisites are absent. Deployment, real recipient delivery, inbox placement and repeated unattended production operation remain outside the demonstrated boundary.
