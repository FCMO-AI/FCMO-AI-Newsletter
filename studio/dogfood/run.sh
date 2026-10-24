#!/bin/sh
# No network, real launcher + HTTP + bare git. All state in a temporary directory (TMPDIR; use a
# disk, not a small tmpfs: it holds several gigabytes) removed on exit, also on failure or signal.
# --browser needs PLAYWRIGHT_MODULE (Node Playwright) and AXE_CORE_PATH (axe.min.js) in the environment.
set -eu
DOGFOOD_REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$DOGFOOD_REPO"
exec python3 -m studio.dogfood.run "$@"
