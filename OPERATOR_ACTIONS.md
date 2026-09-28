# Actions that still require people

The bridge, newsroom build, Pages gates, live identity check, health checks,
incident transitions, and daily email retry are automated in the repository.
The email job is deliberately disabled until its real delivery prerequisites
and the first controlled send have been verified. A green build is not proof of
a fresh public edition or a received email.

| Who | One action | Why a person is required |
|---|---|---|
| Matías | Review the verified integrated candidate and authorize its production release if that authorization has not already been given. | Release judgment; engineering integration and testing are agent work, and existing operator authorization must not be requested again. |

| Javier | Install the read-only ARB GitHub App only if a fresh authorized check shows it is missing. | Repository owner authorization is required for a new installation; HANDOFF records an authenticated production round-trip on September 12, so installation is not established as outstanding. |
| Matías | Restore the bridge App variable/key only if an authorized production check finds them missing or invalid. | The earlier authenticated round-trip is evidence they existed; do not request or rotate credentials based only on this offline checklist. |
| Matías | Approve the publication, translation, privacy and credential policy amendments before opening paid email signup. | Legal and editorial authority cannot be inferred from passing tests. |
| Javier | Provision the Ghost Publisher account and invite the two staff accounts. | Account creation, billing, and human identities cannot be automated here. |
| Matías | Set `GHOST_URL`, `GHOST_ADMIN_API_KEY`, and `FCMO_EMAIL_POSTAL_ADDRESS` in the `email` environment. | Ghost credentials and the legally required postal address are private operator inputs. |
| Javier | Confirm the subscriber privacy notice, consent text, and postal address with the responsible person or counsel. | These are factual and legal attestations; code cannot supply them. |
| Matías | Run one controlled signup and email delivery test in Ghost staging with the designated test mailbox. | Receipt, one-click unsubscribe, SPF/DKIM/DMARC, and Ghost's actual rendering need external observation before production sends are enabled. |
| Matías | Set repository variable `FCMO_EMAIL_ENABLED=true` after that test passes. | This is the final irreversible-send authorization; the job otherwise skips. |
| Javier | Choose and point the public and community domains, then enforce HTTPS in Pages and Ghost. | DNS ownership and domain purchase are external rights and expenses. The Pages URL can remain the interim shareable origin. |
| Matías | Place an Actions-dispatch token in a host-local file with mode `600`. | A separate host needs its own limited credential to revive a stopped GitHub schedule; it must never enter the public checkout. |
| Matías | Run `python3 tools/install_bridge_watchdog.py --token-file PATH_TO_TOKEN_FILE` on the persistent host. | A host owner must authorize its user timer; the script installs an hourly timer and only requests a bridge run after six hours without one. |

After activation, inspect seven consecutive unattended Mexico City days for
freshness, successful bridge → refresh → Pages → live verification, health
alerts, and exactly one delivered Diario per eligible day. `PRODUCTION_STATUS.md`
is a generated snapshot; if its timestamp is old, treat production as unknown.

The host-side watchdog is built but cannot be installed or proved in this
sandbox. Its accepted dispatch request is not counted as a successful run;
the next bridge and Pages receipts must prove recovery. Javier's letters need
his own editorial decision and send action; they cannot be generated in his
voice without approval.

Ghost newsletter creation, theme upload, member onboarding and real delivery
are not yet automated or proved against a live Ghost instance. Keep
`FCMO_EMAIL_ENABLED` unset until those functions and the staging test are
complete. The current static subscription panel remains a launch notice.

## Agent work and evidence still required

The September 26 production snapshot names `ARB_MAIN_RED`; it is not a fresh diagnosis of upstream today. Recheck the actual authorized upstream/production state before assigning a repair. Code repair, checkpoint verification, workflow verification, and repeated-cycle evidence collection are engineering work, not inherently human actions. Offline builder receipts cannot establish current upstream or production health. The integrator must use authorized repository and live-origin evidence before promotion; a local build cannot establish those outcomes.

## Host environment for unattended agent runs (added 2026-09-28)

| Who | One action | Why a person is required |
|---|---|---|
| Claudex operator | Let the `claudex-steward` service copy POSIX ACLs (or drop the default ACLs on its worktrees) so `shutil.copytree` of repository directories stops failing with `EPERM`. | This is a host/systemd permission change outside the repository. Until it is made, test suites run by the steward show about 35 environment-only errors (for example `RealCorpusBacklog`) that are unrelated to the code under test. The paper build itself no longer depends on it: it now copies only file bytes. |
