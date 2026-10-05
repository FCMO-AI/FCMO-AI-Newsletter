#!/bin/sh
# User-level entry; install/configuration belongs to the architect.
set -eu
umask 077
STUDIO_LAUNCH_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
if [ -n "${STUDIO_ENV_FILE:-}" ]; then
    set -a
    . "$STUDIO_ENV_FILE"
    set +a
fi
: "${STUDIO_DATA:?Set STUDIO_DATA to a private directory outside the public checkout}"
: "${STUDIO_ORIGIN:?Set STUDIO_ORIGIN to the private HTTPS origin}"
: "${STUDIO_SESSION_KEY:?Set STUDIO_SESSION_KEY in the private environment}"
STUDIO_REPO=${STUDIO_REPO:-$STUDIO_LAUNCH_ROOT}
STUDIO_BIND=127.0.0.1
STUDIO_PORT=8447
export STUDIO_REPO STUDIO_BIND STUDIO_PORT
cd "$STUDIO_REPO"
exec python3 -m studio.server "$@"
