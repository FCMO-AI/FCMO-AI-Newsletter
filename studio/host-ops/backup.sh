#!/bin/sh
set -eu
: "${STUDIO_REPO:?Set STUDIO_REPO in the private environment file}"
cd "$STUDIO_REPO"
exec python3 -m studio.server.backup "$@"
