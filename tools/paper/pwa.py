#!/usr/bin/env python3
"""Install and validate the small, offline-safe FCMO PWA shell."""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
import shutil


DEFAULT_SOURCE = Path("site-src/assets/pwa")
FAVICON_ICO_B64 = "AAABAAEAICAAAAEAIABmAAAAFgAAAIlQTkcNChoKAAAADUlIRFIAAAAgAAAAIAgGAAAAc3p69AAAAC1JREFUeNrtziEBAAAMAjBS0L/pHwMzMb+0vaUICAgICAgICAgICAgICAisAw84gwRMdc9AuAAAAABJRU5ErkJggg=="
REGISTRATION = "<script data-fcmo-pwa>(function(){if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('./sw.js',{scope:'./'});});}}());</script>"


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def validate_source(source: Path) -> None:
    required = (source / "manifest.webmanifest", source / "sw.js", source / "favicon.svg", source / "icons/icon-192.svg", source / "icons/icon-512.svg")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError("PWA assets missing: " + ", ".join(missing))
    manifest = _read_json(source / "manifest.webmanifest")
    for key in ("name", "short_name", "start_url", "scope", "display", "icons"):
        if key not in manifest:
            raise ValueError(f"manifest missing {key}")
    if manifest["scope"] != "./" or manifest["start_url"] != "./":
        raise ValueError("manifest must stay relative to the Pages base path")
    sw = (source / "sw.js").read_text(encoding="utf-8")
    if "newsroom-status" not in sw or "cache.addAll" not in sw or "cache.put" not in sw:
        raise ValueError("service worker must cache the shell and protect newsroom-status")
    start = sw.index("if (url.pathname.includes(STATUS_MARKER))")
    end = sw.index("if (request.mode ===", start)
    status_block = sw[start:end]
    if "cache.put" in status_block or "caches.open" in status_block:
        raise ValueError("service worker must not cache newsroom-status")


def _register_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "data-fcmo-pwa" in text:
        return
    lower = text.lower()
    marker = "</body>"
    if marker in lower:
        index = lower.rfind(marker)
        text = text[:index] + REGISTRATION + text[index:]
    else:
        text += REGISTRATION
    path.write_text(text, encoding="utf-8")


def build(source: Path, out: Path) -> int:
    validate_source(source)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "manifest.webmanifest", out / "manifest.webmanifest")
    shutil.copy2(source / "sw.js", out / "sw.js")
    shutil.copy2(source / "favicon.svg", out / "favicon.svg")
    if (out / "icons").exists():
        shutil.rmtree(out / "icons")
    shutil.copytree(source / "icons", out / "icons")
    (out / "favicon.ico").write_bytes(base64.b64decode(FAVICON_ICO_B64))
    root_index = out / "index.html"
    registered = 0
    if root_index.is_file():
        _register_html(root_index)
        registered = 1
    print(f"PWA OK manifest={out / 'manifest.webmanifest'} registered_html={registered}")
    return 0


def check(source: Path, out: Path | None = None) -> int:
    validate_source(source)
    if out is not None:
        for path in (out / "manifest.webmanifest", out / "sw.js", out / "favicon.ico"):
            if not path.is_file():
                raise ValueError(f"candidate missing {path}")
        if not _read_json(out / "manifest.webmanifest").get("icons"):
            raise ValueError("candidate manifest has no icons")
    print("PWA source OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the FCMO PWA shell")
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    build_parser.add_argument("--out", type=Path, required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    check_parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        return build(args.source, args.out) if args.command == "build" else check(args.source, args.out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"PWA FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
