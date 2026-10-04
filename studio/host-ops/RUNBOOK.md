# FCMO Studio: installation and recovery

These artifacts are staged in the lane worktree. The architect installs them;
this lane does not enable a host service or a public publication.

1. Choose private data, backup, checkout and environment-file locations. The
   checkout must contain the integrated A1, A2 and B code. Keep data and backups
   outside the public checkout. Copy `studio.env.example` to a private environment
   file (root-owned, Studio group-readable, mode 0640). Set all empty values;
   generate the session key locally. Do not put passwords or tokens in commands,
   reports, public files or agent jobs.
2. Create the private Newsletter clone at `$STUDIO_DATA/clone` before first use.
   The public repository is the origin; only `studio/*` push refs are allowed.
   If Studio has already created a blank local clone, set its origin and fetch
   the public main, then seed it before production use. Never push `draft/*`.
3. Provision each of the two accounts interactively using
   `python3 -m studio.server --add-user javier` and the corresponding command
   for `matias`, with the private environment already loaded. Passwords are
   prompted; scrypt hashes and sessions live only in the private database.
4. Install the user units. Supply an `EnvironmentFile` drop-in pointing to the
   operator's private environment file, and a `ReadWritePaths` drop-in allowing
   the Studio data location. The supplied `%h/.config/fcmo-studio/studio.env`
   location is a portable installation placeholder. Backups use the same
   environment and a separate private backup location. Set modes to 0700/0600.
5. Start Studio with `STUDIO_LIVE_ENABLED=0`. It binds only to loopback. The
   architect configures tailnet-only HTTPS on port 8447, targeting
   `http://127.0.0.1:8447`; never enable Funnel. Verify the tailnet-only status,
   localhost listener, Javier's access and the two distinct personal logins.
   Direct HTTP is for loopback probes; browsers need HTTPS for the secure cookie.
6. Run `bash studio/host-ops/backup.sh --drill "$STUDIO_DRILL_DEST"`, where the
   destination is empty and the private environment includes `STUDIO_REPO`,
   `STUDIO_DATA`, and `STUDIO_BACKUPS`. The drill backs up, verifies every byte,
   restores every draft/checkpoint, starts a server on a free loopback test port,
   and checks health. Run before Javier's first use, then monthly. Enable the
   hourly backup timer only after that proof. Retention is the newest 48
   snapshots plus one per day for the newest 30 days; no remote backup upload.
7. Complete A1/B preview identity and browser acceptance, plus L11 protected
   main and CODEOWNERS acceptance. Resolve Q1/Q5. Only the operator may then
   set `STUDIO_LIVE_ENABLED=1`. Non-English originals stay disabled until Q2
   is adopted in policy; the configuration flag alone is not that decision.

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
