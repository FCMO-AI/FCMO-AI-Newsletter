#!/usr/bin/env python3
"""Check every generated localized page in Chromium at mobile and desktop widths."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module  # noqa: E402

SERVE = ROOT / "tests" / "harness" / "serve.py"
ORACLE = ROOT / "tests" / "harness" / "browser" / "ci_visual.mjs"
REQUIRED_LOCALES = {"en", "es-419", "zh-Hans"}


def load_inputs(root: Path) -> tuple[int, str]:
    routes_file = root / "data" / "routes.json"
    if not routes_file.is_file():
        raise ValueError(f"route manifest not found: {routes_file}")
    rows = json.loads(routes_file.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("route manifest is empty or malformed")
    locales = {row.get("locale") for row in rows if isinstance(row, dict)}
    missing = sorted(REQUIRED_LOCALES - locales)
    if missing:
        raise ValueError(f"route manifest is missing locales: {', '.join(missing)}")
    if any(not isinstance(row, dict) or not isinstance(row.get("path"), str)
           or row.get("locale") not in REQUIRED_LOCALES for row in rows):
        raise ValueError("route manifest contains a malformed or unsupported route")
    config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
    public_origin = config.get("base_url")
    if not isinstance(public_origin, str) or not public_origin.startswith(("http://", "https://")):
        raise ValueError("config/site.json must define an absolute base_url")
    return len(rows), public_origin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="generated publication root (for example publish)")
    parser.add_argument("--base", default="/FCMO-AI-Newsletter/", help="Pages project base path")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"VISUAL CI FAIL: not a directory: {root}")
    try:
        route_count, public_origin = load_inputs(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"VISUAL CI FAIL: {exc}") from exc
    module = resolve_playwright_module()
    if not module:
        raise SystemExit(missing_playwright_message())
    env = os.environ.copy()
    env["PLAYWRIGHT_MODULE"] = module
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--root", str(root), "--base", args.base, "--port", "0"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        line = server.stdout.readline().strip() if server.stdout else ""
        if not line.startswith("SERVING "):
            detail = server.stderr.read() if server.stderr else ""
            raise RuntimeError(f"static server did not start: {line} {detail}".strip())
        base = line.split(maxsplit=1)[1]
        completed = subprocess.run(
            ["node", str(ORACLE), base, str((root / "data" / "routes.json").resolve()), public_origin],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=1800,
        )
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.returncode == 2:
            raise RuntimeError(completed.stderr.strip() or "Playwright/Chromium unavailable")
        if completed.returncode != 0:
            if completed.stderr:
                print(completed.stderr, file=sys.stderr, end="")
            return completed.returncode
        print(f"PASS CI visual gate: routes={route_count}; locales=3; viewports=390x844,1440x900")
        return 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"VISUAL CI FAIL: {exc}") from exc
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
