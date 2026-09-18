#!/usr/bin/env python3
"""Capture compact Chromium screenshots for human visual review in CI artifacts."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
CASES = (
    ("home", "index.html?visual-qa=1#/home"),
    ("archive", "archive.html"),
    ("search", "search.html"),
    ("status", "status.html"),
)
VIEWPORTS = ((390, 844, "mobile"), (1440, 900, "desktop"))


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def browser_path() -> str:
    override = os.environ.get("FCMO_BROWSER")
    if override and (shutil.which(override) or Path(override).is_file()):
        return shutil.which(override) or override
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("visual screenshot capture: no Chromium browser found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("publish"))
    parser.add_argument("out", nargs="?", type=Path, default=Path("visual-qa"))
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    browser = browser_path()

    with serve(root) as base:
        for route, url in CASES:
            for width, height, label in VIEWPORTS:
                target = out / f"{route}-{label}-{width}x{height}.png"
                profile = Path(tempfile.mkdtemp(prefix="fcmo-shot-"))
                try:
                    completed = subprocess.run(
                        [
                            browser,
                            "--headless=new",
                            "--no-sandbox",
                            "--disable-gpu",
                            "--disable-dev-shm-usage",
                            "--disable-background-networking",
                            "--hide-scrollbars",
                            "--virtual-time-budget=2500",
                            f"--window-size={width},{height}",
                            f"--user-data-dir={profile}",
                            f"--screenshot={target}",
                            base + url,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=20,
                    )
                finally:
                    shutil.rmtree(profile, ignore_errors=True)
                if completed.returncode != 0 or not target.is_file() or target.stat().st_size < 1000:
                    raise SystemExit(
                        f"visual screenshot capture failed for {route}/{label}: "
                        f"{completed.stderr[-1200:]}"
                    )
    print(f"Visual QA screenshots OK: {len(CASES) * len(VIEWPORTS)} images -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
