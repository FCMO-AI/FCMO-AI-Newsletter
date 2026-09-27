#!/usr/bin/env sh
set -eu

theme_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
tokens_file="$theme_dir/../../design/tokens.json"
tokens_css="$theme_dir/assets/css/tokens.css"

# A3a owns the canonical token file. B1 only reads it and emits a theme-local
# projection; the fallback keeps the theme buildable in this integration lane.
if [ -f "$tokens_file" ]; then
  python3 - "$tokens_file" "$tokens_css" <<'PY'
import json
import re
import sys
from pathlib import Path

source, target = map(Path, sys.argv[1:])
data = json.loads(source.read_text(encoding="utf-8"))
values = {}

def visit(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            visit(child, path + (str(key),))
    elif isinstance(value, (str, int, float)) and path:
        text = str(value)
        if re.fullmatch(r"#[0-9A-Fa-f]{3,8}|(?:rgb|hsl)a?\([^)]*\)|-?[0-9]+(?:\.[0-9]+)?(?:px|rem|em|%)?", text):
            name = "-".join(re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-") for part in path)
            if name and name not in values:
                values[name] = text

visit(data)
lines = [":root {"]
for name, value in sorted(values.items()):
    lines.append(f"  --token-{name}: {value};")
lines.append("}")
target.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
else
  # Do not mutate or create design/tokens.json from this package.
  test -s "$tokens_css"
fi

if [ "${1:-}" = "--check" ]; then
  test -f "$theme_dir/package.json"
  test -f "$theme_dir/default.hbs"
  test -f "$theme_dir/assets/css/screen.css"
  test -f "$theme_dir/locales/es.json"
  printf '%s\n' "fcmo-comunidad theme OK"
fi
