# FCMO Studio: installation and recovery

The architect installs these artifacts. Follow [ACTIVATION.md](ACTIVATION.md) and
[REPORT-L25.md](../../REPORT-L25.md) for the exact L25
account, CODEOWNERS, ruleset, browser and live acceptance sequence.

1. Choose private data, backup, checkout and environment-file locations. The
   checkout must contain the integrated A1, A2 and B code. Keep data and backups
   outside the public checkout. Copy `studio.env.example` to a private environment
   file (owned by fcmo-agent, mode 0600). Set all empty values;
   generate the session key locally. Do not put passwords or tokens in commands,
   reports, public files or agent jobs.
2. The launcher initializes the private Newsletter clone's public origin if
   needed, fetches public main, and pins the library to a detached immutable
   worktree under `$STUDIO_DATA/snapshots/<commit>`. It refreshes that library
   after a verified Studio publication and on startup. Existing configured
   origins must be the canonical HTTPS public Newsletter repository. Only
   `studio/*` candidate refs can be sent; `draft/*` ancestry stays private.
3. Provision each of the two accounts interactively using
   `sh studio/host-ops/start.sh --add-user javier` and the corresponding command
   for `matias`, with the private environment already loaded. Passwords are
   prompted; scrypt hashes and sessions live only in the private database.
4. Run `sh studio/host-ops/install.sh` as fcmo-agent. It installs the unit in
   `~/.config/systemd/user/`, reloads and enables/starts it, using the private
   `~/.config/fcmo-studio/studio.env`. `rollback.sh` restores the prior unit and
   activation without deleting drafts or logins. Backups use the same
   environment and a separate private backup location. Set modes to 0700/0600.
5. Start `sh studio/host-ops/start.sh` with `STUDIO_LIVE_ENABLED=0` and
   `STUDIO_DRY_RUN=1`. It binds only to loopback. The
   architect configures tailnet-only HTTPS targeting the selected loopback
   port in 8490-8499 (L25: 8490); never enable Funnel. Verify the tailnet-only status,
   localhost listener, Javier's access and the two distinct personal logins.
   Direct HTTP is for loopback probes; browsers need HTTPS for the secure cookie.
6. Run `bash studio/host-ops/backup.sh --drill "$STUDIO_DRILL_DEST"`, where the
   destination is empty and the private environment includes `STUDIO_REPO`,
   `STUDIO_DATA`, and `STUDIO_BACKUPS`. The drill backs up, verifies every byte,
   restores every draft/checkpoint, starts a server on a free loopback test port,
   and checks health. Run before Javier's first use, then monthly. Enable the
   hourly backup timer only after that proof. Retention is the newest 48
   snapshots plus one per day for the newest 30 days; no remote backup upload.
7. Re-run the local bare-remote proof and the full suite, inspect v4 essay/issue
   routes in a real browser, and verify protected main, named code owners and
   the required `publish-gate` with strict up-to-date checks. The local candidate and required PR gate both run the full suite, release
   integrity checks and browser matrix; Pages alone deploys and promotes LKG after exact public
   identity verification. Provision separate gh configuration directories with
   `STUDIO_GH_CONFIG_JAVIER` and `STUDIO_GH_CONFIG_MATIAS`, or supply the named
   fine-grained tokens. Two identical GitHub logins refuse publication. Missing
   credentials never trigger a fallback. No token is extracted from gh.
8. Create, edit and preview in the private Studio, mark each language ready or
   explicitly pending, and obtain the other person's approval. Dry-run mode
   records approval but never advances the publication worker. Stop the server
   before running `python3 -m studio.server.publish --slug "$STUDIO_SLUG" --dry-run`
   with the private environment loaded. It refuses an unreviewed draft, missing
   credentials/protection/LKG, failed gates or changed main. The local candidate
   uses `python3 ops/publish.py --check`; the PR still must pass the real browser
   matrix. Follow `REPORT-STUDIO-LIVE.md` for exact operation/reversal commands.
9. Only after architect acceptance, start with `STUDIO_DRY_RUN=0` and
   `STUDIO_LIVE_ENABLED=1`. This resumes approved publications: fresh main →
   allowlisted candidate → personal branch/PR → other-person review → green
   protected gate → pinned merge → merge-specific Pages → live locale routes.
   A stale base refuses and requires a new review. Non-English originals remain
   disabled until the editorial policy authorizes them.

Restore outside the active data location:

```sh
python3 -m studio.server.backup --restore "$STUDIO_SNAPSHOT" --destination "$STUDIO_NEW_DATA"
```

Reconfigure the restored clone's public origin before resuming publication;
credentials and the session key remain in the private environment. The bundle
contains draft branches and version ancestry. The DB contains acknowledged
uncommitted autosaves, cursors, reviews and publication receipts. Uploaded figures
are immutable blobs copied locally. Pending candidate placement is rebuilt for
the new data location. Restarted publication observes GitHub state before retrying
an unacknowledged action. If no remote evidence confirms an ambiguous write, it
stays unresolved and does not repeat it. The architect must inspect the specific
public branch/PR/review/merge before resolving that boundary; do not clear intent
blindly or switch credentials.

A deployment is confirmed only after all three live routes answer 200 with the
expected article identity. A visibility failure stays `deployed_unverified`;
checks retry at two-minute intervals for thirty minutes. A GitHub refusal never
triggers a different credential. Red checks preserve main and leave the PR open;
a new review closes that prior PR before creating another public candidate.

Emergency rollback requires the exact phrase shown by Studio. Its dispatch is
only a request; it does not erase what readers already saw. The reviewed
withdrawal, with a note in each published language, remains the durable fix.

No draft text appears in audit records or server request logs. The two bootstrap
exceptions to authentication are the login endpoint and static login chrome;
API data, preview HTML and preview publication assets always require a session.
The server serves B's compiled static files read-only and does not manufacture a
replacement UI when the bundle is absent.
