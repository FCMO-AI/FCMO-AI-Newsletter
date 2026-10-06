#!/bin/sh
# Reversible repository ruleset only; does not modify other rulesets.
set -eu
exec python3 "$(dirname "$0")/protect_main.py" "$@"
