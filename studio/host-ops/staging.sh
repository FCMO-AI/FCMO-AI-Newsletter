#!/bin/sh
# Private Studio staging for batteries. Starts a Studio instance from this checkout with a fresh
# temporary data directory, a free loopback port, offline fake GitHub and no live publishing.
# It never touches the live service (port 8490), its data or its environment, nor ports 8491 and 8496.
#
#   sh studio/host-ops/staging.sh [--translation fake|codex]
#       Start in the foreground. Prints the URL, the PID and the battery credentials file. Ctrl-C or
#       TERM stops the instance and deletes its temporary directory.
#   sh studio/host-ops/staging.sh --check [--translation fake|codex]
#       Start, wait for /healthz, smoke-test both battery users (login, refusals, readiness), stop,
#       verify the port is free and the directory is gone. Exit 0 only if every step passed.
#   sh studio/host-ops/staging.sh --stop
#       Stop every instance recorded by an earlier run and delete its temporary directory.
set -u
umask 077

HERE=$(CDPATH='' cd "$(dirname "$0")/../.." && pwd)
WORK_BASE=${TMPDIR:-/tmp}
# State lives in one fixed per-user place, so --stop finds an instance whatever TMPDIR it was started with.
STATE_DIR=${XDG_RUNTIME_DIR:-/tmp}/studio-staging
HEALTH_TIMEOUT=${STAGING_HEALTH_TIMEOUT:-180}
MODE=run
TRANSLATION=fake
PROVIDER=fake
PORT=
WORK=
PID=
STAGING_PASSWORD=

err() { printf 'staging: %s\n' "$*" >&2; }

usage() {
    printf 'usage: sh studio/host-ops/staging.sh [--check | --stop] [--translation fake|codex]\n'
}

# Exit 0 when nothing listens on 127.0.0.1:$1.
port_free() {
    python3 -I -c '
import socket, sys
s = socket.socket()
# SO_REUSEADDR: leftover TIME-WAIT connections do not count, only a live listener does.
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    sys.exit(1)
finally:
    s.close()
' "$1"
}

# First free port: 8497 by default, else the first free port from 8492 up. Never 8490, 8491 or 8496.
pick_port() {
    for p in 8497 $(i=8492; while [ "$i" -le 8599 ]; do echo "$i"; i=$((i + 1)); done); do
        case $p in
            8490|8491|8496) continue ;;
        esac
        if port_free "$p"; then
            echo "$p"
            return 0
        fi
    done
    return 1
}

random_hex() {
    od -An -tx1 -N "$1" /dev/urandom | tr -d ' \n'
}

# Exit 0 when the staging /healthz answers 200.
healthy() {
    python3 -I -c '
import sys, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:%s/healthz" % sys.argv[1], timeout=5) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
' "$PORT"
}

# Stop $PID (only if it really is a Studio server), wait for it, delete $WORK and the state record.
stop_instance() {
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        if tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null | grep -q 'studio.server'; then
            kill "$PID" 2>/dev/null
            n=0
            while kill -0 "$PID" 2>/dev/null && [ "$n" -lt 10 ]; do
                sleep 1
                n=$((n + 1))
            done
            kill -0 "$PID" 2>/dev/null && kill -9 "$PID" 2>/dev/null
        else
            err "pid $PID is not a Studio server; not signalled"
        fi
    fi
    if [ -n "$PID" ]; then
        wait "$PID" 2>/dev/null || true
    fi
    if [ -n "$PORT" ]; then
        rm -f "$STATE_DIR/studio-staging-$PORT.state"
    fi
    case $WORK in
        /*/studio-staging.??????) rm -rf "$WORK" ;;
    esac
    PID=
    WORK=
}

# Create the fresh data directory, the users, and launch the server from this checkout.
start_instance() {
    PORT=$(pick_port) || { err "no free port in 8497 or 8492-8599"; return 1; }
    mkdir -p "$STATE_DIR" || { err "cannot create the state directory"; return 1; }
    WORK=$(mktemp -d "$WORK_BASE/studio-staging.XXXXXX") || { err "cannot create a temporary directory"; return 1; }
    mkdir -p "$WORK/data" "$WORK/bin" "$WORK/home" "$WORK/gh-javier" "$WORK/gh-matias" || return 1
    SESSION_KEY=$(random_hex 24)
    STAGING_PASSWORD=$(random_hex 16)
    printf 'STUDIO_STAGING_PASSWORD=%s\n' "$STAGING_PASSWORD" > "$WORK/battery.env"

    # Offline GitHub: the dogfood fake gh, first on PATH for the server only.
    cp "$HERE/studio/dogfood/fake_gh.py" "$WORK/bin/gh" || return 1

    if ! STAGING_PASSWORD=$STAGING_PASSWORD STUDIO_SESSION_KEY=$SESSION_KEY python3 -I - "$HERE" "$WORK/data" <<'PY'
import os, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from studio.server.auth import Auth
from studio.server.storage import Store
store = Store(Path(sys.argv[2]))
try:
    auth = Auth(store, os.environ['STUDIO_SESSION_KEY'])
    for user in ('javier', 'matias'):
        auth.add_user(user, os.environ['STAGING_PASSWORD'])
finally:
    store.close()
PY
    then
        err "cannot create the battery users"
        stop_instance
        return 1
    fi

    # Clean environment: no operator GH_*, GITHUB_* or live STUDIO_* variables reach the staging server.
    # Real translation needs the operator's Codex login: point CODEX_HOME at it (never copied or printed).
    CODEX_ENV=
    if [ "$PROVIDER" = codex-cli ]; then CODEX_ENV="CODEX_HOME=${CODEX_HOME:-$HOME/.codex}"; fi
    # shellcheck disable=SC2086
    env -i PATH="$WORK/bin:$PATH" HOME="$WORK/home" LANG=C.UTF-8 $CODEX_ENV \
        STUDIO_DATA="$WORK/data" STUDIO_ORIGIN="http://127.0.0.1:$PORT" STUDIO_SESSION_KEY="$SESSION_KEY" \
        STUDIO_PORT="$PORT" STUDIO_BIND=127.0.0.1 STUDIO_REPO="$HERE" \
        STUDIO_LIVE_ENABLED=0 STUDIO_DRY_RUN=1 STUDIO_ALLOW_NON_EN_SOURCE=0 \
        STUDIO_GH_CONFIG_JAVIER="$WORK/gh-javier" STUDIO_GH_CONFIG_MATIAS="$WORK/gh-matias" \
        STUDIO_TRANSLATION_PROVIDER="$PROVIDER" STUDIO_TRANSLATION_TIMEOUT=120 \
        DOGFOOD_ROOT="$WORK" \
        sh "$HERE/studio/host-ops/start.sh" >"$WORK/server.log" 2>&1 &
    PID=$!
    printf 'PID=%s\nPORT=%s\nWORK=%s\n' "$PID" "$PORT" "$WORK" > "$STATE_DIR/studio-staging-$PORT.state"

    waited=0
    while ! healthy; do
        if ! kill -0 "$PID" 2>/dev/null; then
            err "the staging server exited during start (log: $WORK/server.log)"
            stop_instance
            return 1
        fi
        if [ "$waited" -ge "$HEALTH_TIMEOUT" ]; then
            err "no /healthz after ${HEALTH_TIMEOUT}s (log: $WORK/server.log)"
            stop_instance
            return 1
        fi
        sleep 1
        waited=$((waited + 1))
    done
    return 0
}

# Login of both battery users, a refused wrong password, anonymous refusal and readiness.
api_smoke() {
    STAGING_PASSWORD=$STAGING_PASSWORD python3 -I - "$PORT" javier matias <<'PY'
import json, os, sys, urllib.error, urllib.request
port, users, password = sys.argv[1], sys.argv[2:], os.environ['STAGING_PASSWORD']
origin = 'http://127.0.0.1:' + port
failed = []

def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    if not ok:
        failed.append(name)

def call(method, path, body=None, cookie=None):
    headers = {'Origin': origin}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    if cookie:
        headers['Cookie'] = cookie
    request = urllib.request.Request(origin + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()

status, _, _ = call('GET', '/api/pieces')
check('anonymous private API refused (401)', status == 401)
for user in users:
    status, _, _ = call('POST', '/api/login', {'user': user, 'password': password + 'x'})
    check(user + ': wrong password refused', status in (401, 403))
    status, headers, _ = call('POST', '/api/login', {'user': user, 'password': password})
    cookie = (headers.get('Set-Cookie') or '').split(';')[0]
    check(user + ': login 200 with session cookie', status == 200 and cookie != '')
    if status != 200 or not cookie:
        continue
    status, _, raw = call('GET', '/api/publication-readiness', cookie=cookie)
    try:
        readiness = json.loads(raw)
    except ValueError:
        readiness = None
    check(user + ': readiness 200 with credentials list', status == 200 and isinstance(readiness, dict) and 'credentials' in readiness)
    status, _, _ = call('GET', '/api/pieces', cookie=cookie)
    check(user + ': private API 200 with session', status == 200)

sys.exit(1 if failed else 0)
PY
}

cleanup() {
    rc=$?
    trap - EXIT HUP INT TERM
    if [ -n "$PID" ] || [ -n "$WORK" ]; then
        stop_instance
    fi
    exit "$rc"
}

run_foreground() {
    start_instance || return 1
    printf 'Studio staging: http://127.0.0.1:%s/\n' "$PORT"
    printf 'PID: %s\n' "$PID"
    printf 'Battery credentials: %s (users javier and matias, mode 600)\n' "$WORK/battery.env"
    printf 'Stop with Ctrl-C here, or: sh studio/host-ops/staging.sh --stop\n'
    wait "$PID"
    rc=$?
    err "staging server exited with status $rc"
    return "$rc"
}

run_check() {
    rc=0
    if ! start_instance; then
        printf 'FAIL start\n'
        return 1
    fi
    printf 'PASS start: port %s, pid %s, /healthz 200\n' "$PORT" "$PID"
    if api_smoke; then
        printf 'PASS api smoke\n'
    else
        printf 'FAIL api smoke\n'
        rc=1
    fi
    chosen=$PORT
    saved_work=$WORK
    stop_instance
    if port_free "$chosen"; then
        printf 'PASS cleanup: nothing listens on %s\n' "$chosen"
    else
        printf 'FAIL cleanup: something still listens on %s\n' "$chosen"
        rc=1
    fi
    if [ -e "$saved_work" ]; then
        printf 'FAIL cleanup: temporary directory remains\n'
        rc=1
    else
        printf 'PASS cleanup: temporary directory removed\n'
    fi
    return "$rc"
}

run_stop() {
    found=0
    for state in "$STATE_DIR"/studio-staging-*.state; do
        [ -f "$state" ] || continue
        found=1
        PID=$(sed -n 's/^PID=//p' "$state")
        PORT=$(sed -n 's/^PORT=//p' "$state")
        WORK=$(sed -n 's/^WORK=//p' "$state")
        stop_instance
        printf 'stopped staging on port %s\n' "$PORT"
    done
    [ "$found" = 1 ] || printf 'no staging instance recorded\n'
    return 0
}

while [ $# -gt 0 ]; do
    case $1 in
        --check) MODE=check ;;
        --stop) MODE=stop ;;
        --translation)
            [ $# -ge 2 ] || { err "--translation needs fake or codex"; exit 2; }
            TRANSLATION=$2
            shift
            ;;
        --translation=*) TRANSLATION=${1#--translation=} ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
    shift
done

case $TRANSLATION in
    fake) PROVIDER=fake ;;
    codex) PROVIDER=codex-cli ;;
    *) err "unknown translation '$TRANSLATION' (fake or codex)"; exit 2 ;;
esac

case $MODE in
    stop)
        run_stop
        exit $?
        ;;
    check)
        trap cleanup EXIT
        trap 'exit 129' HUP
        trap 'exit 130' INT
        trap 'exit 143' TERM
        run_check
        exit $?
        ;;
    run)
        trap cleanup EXIT
        trap 'exit 129' HUP
        trap 'exit 130' INT
        trap 'exit 143' TERM
        run_foreground
        exit $?
        ;;
esac
