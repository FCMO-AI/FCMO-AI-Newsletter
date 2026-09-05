#!/usr/bin/env python3
"""Autonomous Visual Desk for FCMO AI Newsletter.

The desk never turns an attractive web image into a publishable asset merely because it
was discoverable. Existing sourced images are preserved under the migration allowlist;
new stories receive deterministic FCMO-owned editorial art immediately, while candidate
first-party images may be discovered into an ephemeral work file for later rights-aware
promotion.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OG_IMAGE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I)
OG_IMAGE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.I)
TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)
USER_AGENT = "FCMO-AI-Newsletter-VisualDesk/1.0 (+https://fcmo-ai.github.io/FCMO-AI-Newsletter/)"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def wrap(text: str, limit: int = 38) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if current and len(" ".join(current + [word])) > limit:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines[:4]


def render_svg(record: dict[str, Any], path: Path) -> None:
    title = str(record.get("title") or record.get("id"))
    lines = wrap(title)
    evidence = str(record.get("evidence") or record.get("evidence_class") or "?")
    importance = record.get("importance") or record.get("importance_effective_score") or "?"
    desk = str(record.get("desk") or record.get("primary_desk") or "Research")
    line_markup = "".join(
        f'<text x="78" y="{210 + index * 56}" class="headline">{esc(line)}</text>'
        for index, line in enumerate(lines)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" role="img" aria-labelledby="title desc">
<title id="title">{esc(title)}</title><desc id="desc">FCMO editorial evidence graphic for {esc(title)}.</desc>
<rect width="1200" height="675" fill="#10100e"/><path d="M0 0H1200V675H0Z" fill="none" stroke="#3a3833" stroke-width="2"/>
<path d="M78 104H420" stroke="#FD5204" stroke-width="8"/><text x="78" y="150" class="kicker">FCMO AI NEWSLETTER · {esc(desk.upper())}</text>
{line_markup}
<g transform="translate(78 540)"><text class="meta">EVIDENCE {esc(evidence)}</text><text x="260" class="meta">IMPACT {esc(importance)}/10</text></g>
<path d="M1015 90l64 0-32 55z" fill="#FD5204"/><path d="M1015 584h110" stroke="#FD5204" stroke-width="5"/>
<style>.headline{{font:800 46px Arial,sans-serif;fill:#f2eee6;letter-spacing:-1.5px}}.kicker,.meta{{font:700 20px Consolas,monospace;fill:#9f988e;letter-spacing:2px}}.meta{{fill:#f2eee6}}</style></svg>'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def discover_candidate(url: str) -> dict[str, Any] | None:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=15) as response:
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                return None
            body = response.read(2_000_000).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    match = OG_IMAGE.search(body) or OG_IMAGE_REV.search(body)
    if not match:
        return None
    title_match = TITLE.search(body)
    return {
        "source_page": url,
        "candidate_url": html.unescape(match.group(1)).strip(),
        "source_title": re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip() if title_match else None,
        "rights_state": "UNVERIFIED",
        "publishable": False,
        "reason": "Image discovery is not a reuse license; candidate is quarantined until rights are proven.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--work", type=Path, default=Path("newsroom-work"))
    parser.add_argument("--discover", action="store_true")
    args = parser.parse_args()
    media_path = args.site / "data" / "media.json"
    media = load_json(media_path)
    by_id = {item["id"]: item for item in media}
    briefs = []
    for path in sorted((args.site / "data" / "briefs").glob("FCMO-*.json")):
        doc = load_json(path)
        briefs.append(doc)
    candidates: list[dict[str, Any]] = []
    generated = 0
    for doc in briefs:
        record, brief = doc["record"], doc["brief"]
        identifier = record["id"]
        item = by_id.get(identifier)
        if item is None:
            item = {"id": identifier, "mode": "fcmo_fallback", "sourced": False}
            media.append(item)
            by_id[identifier] = item
        if item.get("sourced") is True or item.get("mode") == "real_preferred":
            continue
        svg_rel = f"assets/story-media/{identifier}.svg"
        render_svg(record, args.site / svg_rel)
        item.clear()
        item.update({
            "id": identifier,
            "mode": "fcmo_generated",
            "sourced": False,
            "image_url": svg_rel,
            "credit": "FCMO AI Newsletter · deterministic editorial graphic",
            "fit": "cover",
            "rights_state": "FCMO_OWNED",
            "license": "FCMO-owned editorial artwork",
            "digital_source_type": "algorithmic_editorial_graphic",
            "ai_generated": False,
            "reason": "No rights-proven first-party image was available; FCMO-owned evidence graphic generated automatically.",
        })
        generated += 1
        if args.discover:
            for source in (brief.get("source_urls") or [])[:3]:
                candidate = discover_candidate(source)
                if candidate:
                    candidate["id"] = identifier
                    candidates.append(candidate)
    media.sort(key=lambda item: item["id"])
    media_path.write_text(json.dumps(media, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.discover:
        args.work.mkdir(parents=True, exist_ok=True)
        (args.work / "media-candidates.json").write_text(
            json.dumps(candidates, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"generated_owned_visuals": generated, "quarantined_candidates": len(candidates)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
