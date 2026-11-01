"""Resolve the Node Playwright package without depending on a machine layout."""
from __future__ import annotations

import os
import unittest
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


def browser_required() -> bool:
    """CI sets FCMO_REQUIRE_BROWSER=1: a missing browser is then a failure, never a silent skip."""
    return os.environ.get("FCMO_REQUIRE_BROWSER", "").strip().lower() in {"1", "true", "yes"}


def browser_unavailable(reason: str | None = None) -> None:
    """Raise the outcome for a browser test that cannot run: SkipTest locally, AssertionError when the browser is required."""
    text = reason or missing_playwright_message()
    if browser_required():
        raise AssertionError(f"FCMO_REQUIRE_BROWSER=1 but the browser tests cannot run: {text}")
    raise unittest.SkipTest(text)
