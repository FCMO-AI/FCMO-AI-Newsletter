"""Resolve the Node Playwright package without depending on a machine layout."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def resolve_playwright_module() -> str | None:
    configured = os.environ.get("PLAYWRIGHT_MODULE")
    if configured:
        return configured
    node = shutil.which("node")
    if not node:
        return None
    result = subprocess.run(
        [
            node,
            "-e",
            "const {createRequire}=require('node:module');"
            "const r=createRequire(process.cwd()+'/.playwright-resolver.cjs');"
            "try { process.stdout.write(r.resolve('playwright')); }"
            "catch (_) { process.exit(1); }",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    module = result.stdout.strip()
    return module if result.returncode == 0 and module else None


def missing_playwright_message() -> str:
    return "BROWSER_UNAVAILABLE: set PLAYWRIGHT_MODULE to the installed Node Playwright module path"
