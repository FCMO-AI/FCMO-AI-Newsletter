#!/usr/bin/env python3
"""Render deterministic 1200x630 locale-specific Open Graph cards in Chromium."""

from __future__ import annotations

import argparse
from html import escape
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.paper.i18n import dek, format_date, headline, label, load_catalogs, truncate
    from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module
else:
    from .i18n import dek, format_date, headline, label, load_catalogs, truncate
    from .playwright_module import missing_playwright_message, resolve_playwright_module

ROOT = Path(__file__).resolve().parents[2]
CHROME_JS = """
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
const require=createRequire(import.meta.url), manifest=JSON.parse(await readFile(process.argv[2],'utf8'));
const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||undefined,args:['--disable-breakpad','--disable-crash-reporter','--disable-crashpad']});
for(const item of manifest){const page=await browser.newPage({viewport:{width:1200,height:630},deviceScaleFactor:1});await page.goto(item.url,{waitUntil:'networkidle'});await page.screenshot({path:item.out,type:'png',animations:'disabled'});await page.close()}
await browser.close();
"""


def _size(title: str) -> int:
    length = len(title)
    if length <= 58:
        return 64
    if length <= 82:
        return 56
    if length <= 108:
        return 49
    return 43


def _card(template: str, *, story: dict, locale: dict, catalog: dict) -> str:
    code = locale["code"]
    values = {
        "LANG": locale["html_lang"],
        "DATE": format_date(story["event_at"], catalog, precision=story.get("date_precision", "day")),
        "EVIDENCE": label(catalog, "evidence_class", story.get("evidence_class"), fallback="FCMO AI"),
        "BEAT": label(catalog, "beat", story.get("beat"), fallback="FCMO AI"),
        "HEADLINE": headline(story, code, catalog),
        "DEK": truncate(dek(story, code, catalog), 180),
        "SIZE": str(_size(headline(story, code, catalog))),
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value if key == "SIZE" else escape(str(value)))
    return template


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _find_chrome() -> str | None:
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    node = shutil.which("node")
    module = resolve_playwright_module()
    if not node or not module:
        return None
    result = subprocess.run([node, "-e", "const {chromium}=require(process.argv[1]);process.stdout.write(chromium.executablePath())", module], text=True, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 and Path(result.stdout).is_file() else None


def generate_all(payload: dict, out: Path, *, chrome_path: str | None = None) -> int:
    node = shutil.which("node")
    module = resolve_playwright_module()
    chrome = chrome_path or _find_chrome()
    if not node or not module or not chrome:
        if not module:
            raise RuntimeError(missing_playwright_message())
        raise RuntimeError("BROWSER_UNAVAILABLE: Node or Chromium is missing")
    catalogs = load_catalogs(ROOT)
    config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
    template = (ROOT / "tools" / "paper" / "og_card.html").read_text(encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    with tempfile.TemporaryDirectory(prefix="fcmo-og-") as temp_name:
        temp = Path(temp_name)
        for story in payload["stories"]:
            for locale in config["locales"]:
                html_path = temp / locale["code"] / f"{story['id']}.html"
                png_path = out / locale["code"] / f"{story['id']}.png"
                html_path.parent.mkdir(parents=True, exist_ok=True)
                png_path.parent.mkdir(parents=True, exist_ok=True)
                html_path.write_text(_card(template, story=story, locale=locale, catalog=catalogs[locale["code"]]), encoding="utf-8")
                manifest.append({"url": html_path.resolve().as_uri(), "out": str(png_path.resolve())})
        manifest_path = temp / "manifest.json"
        script_path = temp / "render.mjs"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        script_path.write_text(CHROME_JS, encoding="utf-8")
        env = {**os.environ, "PLAYWRIGHT_MODULE": module, "CHROME_PATH": chrome}
        result = subprocess.run([node, str(script_path), str(manifest_path)], text=True, capture_output=True, env=env, check=False)
        if result.returncode:
            detail = (result.stderr or result.stdout).strip().splitlines()
            blocked = next((line for line in detail if "Operation not permitted" in line), "")
            summary = blocked.strip() or next((line.strip() for line in detail if "browserType.launch:" in line), "")
            raise RuntimeError("BROWSER_UNAVAILABLE: " + (summary or f"Chromium exit {result.returncode}"))
    for item in manifest:
        path = Path(item["out"])
        if png_dimensions(path) != (1200, 630):
            raise ValueError(f"wrong PNG dimensions: {path} {png_dimensions(path)}")
        if path.stat().st_size > 200 * 1024:
            raise ValueError(f"OG card exceeds 200 KB: {path} {path.stat().st_size}")
    return len(manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stories", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--chrome-path")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.stories.read_text(encoding="utf-8"))
        count = generate_all(payload, args.out, chrome_path=args.chrome_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"OG FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"OG OK cards={count} size=1200x630 max_bytes=204800")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
