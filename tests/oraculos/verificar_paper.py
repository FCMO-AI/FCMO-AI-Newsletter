#!/usr/bin/env python3
"""Render the three paper front pages at desktop/mobile before deployment."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests" / "harness" / "browser"
SERVE = ROOT / "tests" / "harness" / "serve.py"
PLAYWRIGHT = Path("/srv/fcmo/agents/work/newsletter/browser/node_modules/playwright")


def run_check(name: str, urls: list[str], extra: list[str], env: dict[str, str]) -> None:
    command = ["node", str(HARNESS / name), *urls, "--viewport", "1440x900", "--viewport", "390x844", *extra]
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=420)
    if completed.returncode == 2:
        raise RuntimeError(completed.stderr.strip() or f"{name}: browser unavailable")
    if completed.returncode != 0:
        try: detail = json.dumps(json.loads(completed.stdout), ensure_ascii=False)[:4000]
        except ValueError: detail = (completed.stdout + completed.stderr)[-4000:]
        raise AssertionError(f"{name} failed: {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    if not args.root.is_dir(): raise SystemExit(f"PAPER ORACLE FAIL: not a directory: {args.root}")
    env = os.environ.copy(); env.setdefault("PLAYWRIGHT_MODULE", str(PLAYWRIGHT))
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--root", str(args.root.resolve()), "--base", "/FCMO-AI-Newsletter/", "--port", "0"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        line = server.stdout.readline().strip() if server.stdout else ""
        if not line.startswith("SERVING "):
            error = server.stderr.read() if server.stderr else ""
            raise RuntimeError(f"static server did not start: {line} {error}".strip())
        base = line.split(maxsplit=1)[1]
        urls = [base, base + "es/", base + "zh/"]
        run_check("first_screen.mjs", urls, [], env)
        run_check("overflow.mjs", urls, [], env)
        # Font-size/accessibility baseline without adding axe-core as a dependency.
        # The full V4 axe run remains a release-level check once axe-core is provided.
        run_check("axe.mjs", urls, ["--no-axe", "--min-font", "12"], env)
    except (AssertionError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"PAPER ORACLE FAIL: {exc}") from exc
    finally:
        server.terminate()
        try: server.wait(timeout=10)
        except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=10)
    print("PASS 3 locales x 2 viewports")
    return 0


if __name__ == "__main__": raise SystemExit(main())
