# Studio live publication — local implementation and proof

2026-10-05 UTC · branch `c5/studio-live` · implementation `031c8d6`; recovery fix `a9744a4`.

Studio now has a real, protected GitHub publishing path and a user-level launcher.
The offline end-to-end test writes an essay and a curated edition to a bare git
remote, then rebuilds the remote's actual main commit and verifies the edition's
three locale routes. GitHub review/check/Pages responses in that test remain
explicit control-plane doubles. No external push, merge, deployment, service
installation or production-visibility claim is made.

## Integration and release boundary

- Merged the available `origin/main` (`3bdf00e`) into this branch at `f5ab187`.
  No fetch or mutation of the real main/origin was performed. v4's public chrome,
  CSS, mobile fixes, freshness rules, citation history and published data win.
  Builder conflicts preserve Studio editorial input **and** v4 citation retention
  and historical-edition redirects. The fixture manifest is an additive union.
- `ops/publish.py --check` reconstructs the committed Story/status/editorial input,
  requires an existing LKG commit, runs agent hygiene and all fourteen publication
  gates. It cannot push or deploy. Local checks do not replace the PR browser gate.
- The existing validation workflow now supplies the actual `publish-gate` check.
  It builds editorial changes, preserves browser validation and identity generation,
  and has read-only permissions. Pages triggers for `editorial/**`, includes editorial
  input, and preserves its existing browser, exact public-origin, LKG-promotion and
  rollback jobs. LKG recovery includes editorial records from the LKG checkout
  when its renderer supports them; pre-Studio LKG remains recoverable. A separate
  shell regression runs both renderer contracts (red commit `b64c8d9`).
- Studio reads the newsroom library through a detached public-commit snapshot in
  its private store. Startup and successful publication refresh it. Changed snapshot
  bytes refuse reuse. Publication always starts from freshly fetched public main;
  only the selected allowlisted piece or issue is copied. Draft ancestry and all
  other files stay private. The sanitized ARB/corpus contract is preserved.
- The real server uses the host's `gh` credential without extracting its token, or
  the existing named fine-grained token variables. Author/reviewer identities must
  differ. Missing credentials, changed main, failed local/public checks and absent
  active protections refuse publication. Writes retain intent/reconciliation; an
  ambiguous response does not cause a blind resend. Candidate branches cannot
  overwrite an existing ref. Fetch and push destinations are restricted to the
  public Newsletter repository.
- `studio/host-ops/start.sh` forces `127.0.0.1:8447`. The optional user unit calls
  that launcher. Nothing was installed. `STUDIO_DRY_RUN=1` allows private approval
  but suppresses the publication worker even if live is otherwise enabled.

## Credential and specification boundary

`gh` is installed, but `gh auth status --hostname github.com` reported no logged-in
GitHub host in this execution environment. No token or credential file was read
or printed. The alternative credential names are `GH_TOKEN_JAVIER` and
`GH_TOKEN_MATIAS`; their availability and permissions were not inspected. The
preferred host configuration uses `STUDIO_GH_CONFIG_JAVIER` and
`STUDIO_GH_CONFIG_MATIAS` with two distinct GitHub identities. A single host account
cannot substitute for the other person's approval.

The requested `../../STUDIO-SPEC.md`, `../../STUDIO-INT.md` and `../../reports` are
absent from this environment. A text question requesting the accessible spec path
was issued. The checked-in A1/A2/B/integration reports and implemented contracts
were read instead; this does **not** establish conformity to the missing binding
specification. The architect must supply and compare it before accepting this lane.

The repository does not yet supply `.github/CODEOWNERS`. The architect must use the
actual GitHub handles to configure editorial owners and active main rules requiring
one other-person approval, code-owner review, dismissal of stale reviews,
last-push approval and strict `publish-gate`, with no bypass actors. Studio refuses
missing protections; this lane does not configure them remotely.

## Evidence and replay

Red-first commit `b89b1a4` failed on missing publish/check and launcher entrypoints,
missing editorial workflow wiring and missing credential preflight. Its initial
reused-test method name was corrected to the actual existing adversarial test.
Implementation is committed at `031c8d6`.

Executed evidence:

- Final full suite on the completed worktree: **670 tests, no failures/errors,
  four skips, 235.113 s**. The skips are three existing browser-dependent
  cases and the inapplicable absent-renderer negative. All stateful refresh
  oracles ran; no skip environment was added.
- Bare-remote essay **and** issue journey: passed. Actual git transport and merge
  land on the local remote; a clean clone rebuilds both exact committed records,
  verifies essay content and all three issue routes with fourteen gates.
- Six credential/base/dry-run/snapshot negative controls: passed.
- Focused preview/publication/integration tests: 24 tests, no failures/errors, one inapplicable
  absent-renderer negative skipped. Positive authenticated preview byte identity ran.
- Issue version/conflict/published-tree tests: 3 passed.
- Contract fixture validation: 57 passed.
- Site build: 510 routes; agent hygiene passed; publication gates 14/14.
- Browser oracle: refused with `BROWSER_UNAVAILABLE` (Playwright not installed).
  No final-form visual acceptance, zero-overflow claim or live-site proof is made.
- Browser bundle source/artifact integrity: passed; no frontend source was changed.
- Python compilation, launcher shell syntax/real `--help` entry, and
  `git diff --check`: passed.

Ignored evidence lives under `_audit/studio-live/`. The first full-suite run failed
on an older mock's absent main ref and the in-progress edition fixture. The mock
was updated to represent real main, the bare test uses the actual issue checker,
and clean-checkout test log directories are now created explicitly. No publication
gate was weakened.

Re-run from this checkout with a normal temporary directory outside the checkout:

```sh
python3 -m unittest discover -s tests
python3 -m unittest tests.test_studio_live tests.test_studio_integration tests.test_studio_preview -v
python3 tests/harness/validate.py --all-fixtures
python3 ops/publish.py --check
python3 tests/oraculos/verificar_paper.py publish
python3 -c 'from pathlib import Path; from studio.server.bundle import ready; assert ready(Path.cwd())'
git diff --check
```

The browser command requires the host's installed `PLAYWRIGHT_MODULE` and Chromium.
Inspect essay and edition routes in EN/es-419/zh-Hans at 390 and 1440 as well as the
Studio itself before making a visual claim. The public site remains unverified.

## Exact host activation commands

These are architect/operator commands, **not executed by this lane**. Start in the
accepted Newsletter checkout. All data, backups, sessions and gh configuration stay
outside the public checkout. Set `STUDIO_HTTPS_ORIGIN` to the architect's private
HTTPS origin first; tailnet routing/HTTPS remains the architect's responsibility.

Create a new private environment file without printing a session key:

```sh
export STUDIO_REPO="$PWD"
export STUDIO_ENV_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/fcmo-studio/studio.env"
# Supply the real private HTTPS origin, e.g. via an existing host environment.
: "${STUDIO_HTTPS_ORIGIN:?Set the private HTTPS origin}"
python3 - <<'PY'
import os, secrets, shlex
from pathlib import Path
repo = Path(os.environ['STUDIO_REPO']).resolve()
envfile = Path(os.environ['STUDIO_ENV_FILE'])
envfile.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
private = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'fcmo-studio'
config = envfile.parent
values = {
    'STUDIO_REPO': str(repo), 'STUDIO_DATA': str(private / 'data'),
    'STUDIO_BACKUPS': str(private / 'backups'),
    'STUDIO_ORIGIN': os.environ['STUDIO_HTTPS_ORIGIN'],
    'STUDIO_SESSION_KEY': secrets.token_urlsafe(48),
    'STUDIO_BIND': '127.0.0.1', 'STUDIO_PORT': '8447',
    'STUDIO_LIVE_ENABLED': '0', 'STUDIO_DRY_RUN': '1',
    'STUDIO_ALLOW_NON_EN_SOURCE': '0',
    'STUDIO_GH_CONFIG_JAVIER': str(config / 'gh-javier'),
    'STUDIO_GH_CONFIG_MATIAS': str(config / 'gh-matias'),
}
fd = os.open(envfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write(''.join(k + '=' + shlex.quote(v) + '\n' for k, v in values.items()))
private.mkdir(parents=True, exist_ok=True, mode=0o700)
PY
set -a
. "$STUDIO_ENV_FILE"
set +a
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh auth login --hostname github.com --git-protocol https --web
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh auth login --hostname github.com --git-protocol https --web
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh api user --jq .login
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh api user --jq .login
sh studio/host-ops/start.sh --add-user javier
sh studio/host-ops/start.sh --add-user matias
sh studio/host-ops/start.sh
```

The two login commands require the corresponding people to sign in to distinct
accounts. They print no token. Fine-grained tokens are an alternative supplied
privately by the host environment under the named variables; do not provide their
values to an agent, command line, report or repository. Do not select another
credential after a refusal. Direct loopback probes use HTTP; browser access uses
the private HTTPS origin and the existing Secure session cookie.

In another terminal, prove the launcher boundary:

```sh
ss -ltn | rg '127\.0\.0\.1:8447'
curl --fail --silent http://127.0.0.1:8447/healthz
curl --silent --output /dev/null --write-out '%{http_code}\n' http://127.0.0.1:8447/api/pieces
```

Expected: one loopback listener, health OK, unauthenticated API 401. In Studio,
create a draft, edit and preview it, mark language readiness deliberately, request
review as the author and approve as the other person. Dry-run mode holds it at
`approved`. Stop the foreground server with Ctrl-C before running the dry-run:

```sh
export STUDIO_SLUG='the-actual-approved-slug'
set -a
. "$STUDIO_ENV_FILE"
set +a
python3 -m studio.server.publish --slug "$STUDIO_SLUG" --dry-run
```

This checks the reviewed revision, two GitHub identities, protections, LKG,
fresh public base, build and gates. It creates only a local candidate. Any refusal
must be fixed before continuing. The server lock also refuses a dry-run while the
server is running. Verify that the selected slug is the only approved queue entry:

```sh
python3 - <<'PY'
import os, sqlite3
from pathlib import Path
with sqlite3.connect(Path(os.environ['STUDIO_DATA']) / 'studio.sqlite') as db:
    queued = db.execute("SELECT slug FROM publications WHERE state NOT IN ('published','failed')").fetchall()
assert queued == [(os.environ['STUDIO_SLUG'],)], 'Resolve the other queued publications first'
PY
STUDIO_ENV_FILE= STUDIO_DRY_RUN=0 STUDIO_LIVE_ENABLED=1 sh studio/host-ops/start.sh
```

The empty `STUDIO_ENV_FILE` prevents reloading the dry-run defaults over these
explicit overrides; the previously loaded private variables remain exported.
This command resumes the approved publication. Watch the Studio receipt, its PR
and the merge-specific Pages run. Success is `published` with all three verified
URLs, and a successful Pages identity/LKG result. A stale base requires a new
review; an ambiguous write requires reconciliation before another attempt.

## Reverse each step

- Stop a foreground Studio with Ctrl-C. Restart with the private environment's
  defaults (`sh studio/host-ops/start.sh`) to return to held dry-run publication.
  Private drafts, revisions and receipts remain intact. No installed service needs
  removal because this lane installed none.
- A dry-run creates no remote effect. With Studio stopped, remove its candidate
  worktree/branch, preserving the review and draft. The IDs below come from the
  private journal; no draft text or credential is printed:

```sh
python3 - <<'PY'
import json, os, sqlite3, subprocess
from pathlib import Path
root = Path(os.environ['STUDIO_DATA'])
with sqlite3.connect(root / 'studio.sqlite') as db:
    row = db.execute('SELECT id,payload_json,state FROM publications WHERE slug=? ORDER BY rowid DESC LIMIT 1', (os.environ['STUDIO_SLUG'],)).fetchone()
assert row and row[2] == 'approved', 'Cleanup is only for an untransported dry-run'
branch = json.loads(row[1])['branch']
candidate = root / 'candidates' / row[0]
if candidate.exists():
    subprocess.run(['git', '-C', str(root / 'clone'), 'worktree', 'remove', '--force', str(candidate)], check=True)
    subprocess.run(['git', '-C', str(root / 'clone'), 'branch', '-D', branch], check=True)
PY
```

- Before a merge, close the observed public PR as its author; retain the publication
  receipt and inspect any unresolved effect rather than clearing intent. Use the
  real PR number and the author's gh configuration:

```sh
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh pr close "$STUDIO_PR_NUMBER" --repo FCMO-AI/FCMO-AI-Newsletter
```

  Use the Matías configuration when he is the author. Do not delete draft history,
  force main or force a replacement publication. If main already merged, a PR close
  does not reverse the public commit: submit a reviewed correction/withdrawal or
  reviewed revert through the same required check.
- For a failed or wrong deployment, request the existing Pages recovery operation:

```sh
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh workflow run pages.yml --repo FCMO-AI/FCMO-AI-Newsletter --ref main -f operation=rollback
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh run list --repo FCMO-AI/FCMO-AI-Newsletter --workflow pages.yml --limit 5
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh run watch "$STUDIO_ROLLBACK_RUN_ID" --repo FCMO-AI/FCMO-AI-Newsletter --exit-status
```

  This requests recovery to the **current** live-verified LKG; after a successful
  publication LKG may already include the new piece. Use a reviewed source revert
  or withdrawal for such a publication. The workflow's public identity check proves
  serving; a dispatch alone does not. Recovery cannot erase what readers saw.
- Reverse local gh account provisioning with the matching configuration:

```sh
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_JAVIER" gh auth logout --hostname github.com
GH_CONFIG_DIR="$STUDIO_GH_CONFIG_MATIAS" gh auth logout --hostname github.com
```

  Logout removes local authentication; token revocation is a separate account action.
  Keep the private environment/data until the backup/restore drill passes. To remove
  the environment from the active location without destroying recovery data:

```sh
mv "$STUDIO_ENV_FILE" "$STUDIO_ENV_FILE.disabled"
unset STUDIO_SESSION_KEY GH_TOKEN_JAVIER GH_TOKEN_MATIAS
```

If the architect chooses the optional service later, its reversal is
`systemctl --user disable --now fcmo-studio.service`; installation and its private
path permissions remain architect work.

Resumen: publicación real implementada y probada contra Git bare, con edición
trilingüe y controles de rechazo. Sin push externo ni instalación; faltan la
especificación accesible, aceptación en navegador y credenciales/protecciones reales
antes de afirmar que Studio publica correctamente en producción.
