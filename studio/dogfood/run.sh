#!/bin/sh
# No network, real launcher + HTTP + bare git. All state in a temporary directory,
# removed on exit (also on failure or signal). Browser checks and the strict gate's
# visual oracle need Playwright: set PLAYWRIGHT_MODULE, or one of the known host copies is used.
set -eu
DOGFOOD_REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$DOGFOOD_REPO"
if [ -z "${PLAYWRIGHT_MODULE:-}" ]; then
  for candidate in /var/tmp/kui-v1/node_modules/playwright /var/tmp/kui-voz-deps/node_modules/playwright; do
    if [ -d "$candidate" ]; then PLAYWRIGHT_MODULE=$candidate; export PLAYWRIGHT_MODULE; break; fi
  done
fi
exec python3 -m studio.dogfood.run "$@"
