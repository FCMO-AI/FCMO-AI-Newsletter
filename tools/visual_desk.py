#!/usr/bin/env python3
"""Autonomous visual desk for FCMO AI Newsletter.

The desk prefers reusable first-party/public evidence images only when reuse
rights are machine-verifiable. Otherwise it generates an original deterministic
FCMO explanatory SVG, so a missing/ambiguous license never blocks publication
and never becomes an excuse to hotlink questionable art.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PERMISSIVE_LICENSE = re.compile(
    r"https?://creativecommons\.org/(?:licenses/(?:by|by-sa)/(?:[0-9.]+/)?|publicdomain/(?:zero|mark)/(?:[0-9.]+/)?)",
    re.I,
)
OG_IMAGE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
OG_IMAGE_REVERSED = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\']',
    re.I,
)
LICENSE_LINK = re.compile(
    r'<a[^>]+(?:rel=["\'][^"\']*license[^"\']*["\'][^>]+href|href)=["\']([^"\']+)["\']',
    re.I,
)


def load_briefs(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        brief = obj.get("brief")
        if isinstance(brief, dict):
            rows.append(brief)
    return rows


def fetch_text(url: str) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FCMO-AI-Newsletter-VisualDesk/1.0 (+public editorial sourcing)"},
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type and "text" not in content_type:
            return response.geturl(), ""
        data = response.read(1_500_000)
        return response.geturl(), data.decode("utf-8", errors="replace")


def discover_licensed_image(source_urls: list[str]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    rejected: list[dict[str, str]] = []
    for source in source_urls[:6]:
        try:
            final_url, text = fetch_text(source)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            rejected.append({"source": source, "reason": f"fetch_failed:{type(exc).__name__}"})
            continue
        if not text:
            rejected.append({"source": source, "reason": "not_html"})
            continue
        licenses = []
        for candidate in LICENSE_LINK.findall(text):
            absolute = urllib.parse.urljoin(final_url, candidate)
            if PERMISSIVE_LICENSE.search(absolute):
                licenses.append(absolute)
        licenses.extend(x.group(0) for x in PERMISSIVE_LICENSE.finditer(text))
        image_match = OG_IMAGE.search(text) or OG_IMAGE_REVERSED.search(text)
        if not image_match:
            rejected.append({"source": source, "reason": "no_story_image_metadata"})
            continue
        if not licenses:
            rejected.append({"source": source, "reason": "reuse_rights_not_machine_verifiable"})
            continue
        image_url = urllib.parse.urljoin(final_url, html.unescape(image_match.group(1)))
        return {
            "mode": "licensed_source",
            "sourced": True,
            "rights_state": "PERMISSIVE_LICENSE",
            "image_url": image_url,
            "source_page": final_url,
            "license": "permissive Creative Commons / public-domain declaration",
            "license_url": sorted(set(licenses))[0],
            "reuse_basis": "machine-verifiable permissive license on the source page",
            "credit": urllib.parse.urlparse(final_url).netloc,
            "fit": "contain",
        }, rejected
    return None, rejected


def svg_for(brief: dict[str, Any]) -> str:
    title = html.escape(str(brief.get("title") or "FCMO AI Research"))
    evidence = html.escape(str(brief.get("evidence_class") or brief.get("evidence") or "—"))
    importance = html.escape(str(brief.get("importance_effective_score") or brief.get("importance_score") or "—"))
    desk = html.escape(str(brief.get("primary_desk") or "research").replace("_", " ").upper())
    # Footnote: SVG stays text-only so the repository's current public-tree
    # validator can inspect it for secrets and provenance like every other file.
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="t d">
<title id="t">{title}</title>
<desc id="d">FCMO original editorial explainer for {title}. Evidence {evidence}; impact {importance}/10.</desc>
<rect width="1600" height="900" fill="#0B0B0C"/>
<circle cx="1320" cy="170" r="310" fill="#FD5204" opacity=".18"/>
<circle cx="1450" cy="780" r="430" fill="#FFFFFF" opacity=".035"/>
<path d="M0 710 C330 560 490 810 790 650 S1260 420 1600 600" fill="none" stroke="#FD5204" stroke-width="16"/>
<text x="110" y="120" font-family="Arial,Helvetica,sans-serif" font-size="34" letter-spacing="8" fill="#FD5204">FCMO AI NEWSLETTER</text>
<text x="110" y="198" font-family="Arial,Helvetica,sans-serif" font-size="25" letter-spacing="5" fill="#B8B8BC">{desk}</text>
<foreignObject x="110" y="270" width="1120" height="330">
  <div xmlns="http://www.w3.org/1999/xhtml" style="font:700 68px/1.08 Arial,Helvetica,sans-serif;color:#fff">{title}</div>
</foreignObject>
<text x="110" y="790" font-family="Arial,Helvetica,sans-serif" font-size="28" fill="#FFFFFF">EVIDENCE {evidence} · IMPACT {importance}/10</text>
<text x="110" y="838" font-family="Arial,Helvetica,sans-serif" font-size="20" fill="#99999F">FCMO original editorial graphic · not source evidence</text>
</svg>"""


def validate_media_rows(rows: list[dict[str, Any]], expected_ids: set[str], site: Path) -> None:
    """Prove every published visual has a current, machine-checkable reuse basis."""
    errors: list[str] = []
    ids = [str(row.get("id") or "") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not rid for rid in ids):
        errors.append("every media row must be an object with a non-empty id")
    if len(set(ids)) != len(ids):
        errors.append("duplicate media ids")
    if set(ids) != expected_ids:
        errors.append(f"media ids do not match briefs: missing={sorted(expected_ids-set(ids))} extra={sorted(set(ids)-expected_ids)}")

    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "<missing-id>")
        mode = row.get("mode")
        if mode == "licensed_source":
            if row.get("sourced") is not True or row.get("rights_state") != "PERMISSIVE_LICENSE":
                errors.append(f"{rid}: licensed source lacks sourced/rights state")
            license_url = str(row.get("license_url") or "")
            if not PERMISSIVE_LICENSE.search(license_url):
                errors.append(f"{rid}: license_url is not a recognized permissive reuse declaration")
            for key in ("image_url", "source_page", "license_url", "reuse_basis", "credit"):
                if not str(row.get(key) or "").strip():
                    errors.append(f"{rid}: licensed source lacks {key}")
        elif mode == "fcmo_explainer":
            if row.get("sourced") is not False or row.get("generated") is not True:
                errors.append(f"{rid}: FCMO explainer provenance flags are inconsistent")
            if row.get("rights_state") != "FCMO_OWNED" or row.get("evidence_image") is not False:
                errors.append(f"{rid}: FCMO explainer rights/evidence state is inconsistent")
            prefix = "/FCMO-AI-Newsletter/assets/story-media/"
            image_url = str(row.get("image_url") or "")
            if not image_url.startswith(prefix):
                errors.append(f"{rid}: FCMO explainer must use a local story-media asset")
            else:
                asset = site / "assets" / "story-media" / image_url.removeprefix(prefix)
                if not asset.is_file():
                    errors.append(f"{rid}: FCMO explainer asset is missing from the publication tree")
        else:
            errors.append(f"{rid}: unsupported media mode {mode!r}")

    if errors:
        raise ValueError("media rights gate FAILED: " + "; ".join(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-src", type=Path, default=Path("release-src"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--offline", action="store_true", help="skip network discovery and exercise deterministic fallback")
    args = parser.parse_args(argv)

    media_path = args.release_src / "data" / "media.json"
    old = json.loads(media_path.read_text(encoding="utf-8")) if media_path.exists() else []
    old_by_id = {row.get("id"): row for row in old if isinstance(row, dict)}
    assets = args.site / "assets" / "story-media"
    assets.mkdir(parents=True, exist_ok=True)

    briefs = load_briefs(args.release_src)
    result = []
    discovered = generated = 0
    for brief in briefs:
        rid = brief["id"]
        previous = old_by_id.get(rid) or {}
        previous_license = str(previous.get("license_url") or "")
        if (
            previous.get("mode") == "licensed_source"
            and previous.get("sourced") is True
            and PERMISSIVE_LICENSE.search(previous_license)
            and previous.get("reuse_basis")
        ):
            row = dict(previous)
            row["id"] = rid
            row["rights_state"] = "PERMISSIVE_LICENSE"
            result.append(row)
            continue

        found = None
        rejected: list[dict[str, str]] = []
        if not args.offline:
            found, rejected = discover_licensed_image(list(brief.get("source_urls") or []))
        if found:
            row = {"id": rid, **found, "provenance_checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
            if rejected:
                row["rejected_candidates"] = rejected
            discovered += 1
        else:
            asset_rel = f"assets/story-media/{rid}.svg"
            (args.site / asset_rel).write_text(svg_for(brief), encoding="utf-8")
            row = {
                "id": rid,
                "mode": "fcmo_explainer",
                "sourced": False,
                "generated": True,
                "rights_state": "FCMO_OWNED",
                "image_url": f"/FCMO-AI-Newsletter/{asset_rel}",
                "credit": "FCMO AI Research Desk",
                "license": "FCMO original editorial graphic",
                "reuse_basis": "original publication-owned artwork",
                "fit": "cover",
                "evidence_image": False,
                "reason": "No source image with machine-verifiable permissive reuse rights was stronger than an original FCMO explainer."
            }
            if rejected:
                row["rejected_candidates"] = rejected
            generated += 1
        result.append(row)

    # Footnote: validation happens before media.json is replaced. A bad rights
    # receipt therefore cannot partially update the canonical publication state.
    validate_media_rows(result, {str(brief["id"]) for brief in briefs}, args.site)
    media_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"visual desk OK; licensed={discovered}; generated={generated}; total={len(result)}; rights=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
