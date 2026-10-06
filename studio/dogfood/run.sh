#!/bin/sh
# No network, real launcher + HTTP + bare git. All state in a temporary directory.
set -eu
DOGFOOD_REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$DOGFOOD_REPO"
exec python3 -m studio.dogfood.run "$@"
