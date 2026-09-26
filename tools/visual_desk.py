#!/usr/bin/env python3
"""FCMO AI visual desk: a rights-proven story image, or an FCMO explainer.

A discoverable image is not a publishable one (MEDIA_POLICY.md). The desk reads
each story's cited sources and accepts a picture only when the picture itself
carries a machine-verifiable permissive licence:

* a Wikimedia Commons file whose own file metadata (Commons API
  ``extmetadata``) names CC BY, CC BY-SA or CC0 and an author; or
* a schema.org ``ImageObject`` on the source page whose own ``license`` is a
  CC BY, CC BY-SA, CC0 or Public Domain Mark URL and which names a credit.

A licence link somewhere on a page licenses that page's article, not the site's
share image, so ``og:image`` plus a page licence proves nothing. Site chrome
(logos, icons, generated share cards, one image repeated across pages) is
refused before any licence is considered. An accepted image is downloaded,
checked (raster type, size, landscape hero shape) and stored under
``site/media/``: the paper never hotlinks. Everything else falls back to a
language-neutral FCMO explainer from ``site-src/assets/explainers/``, credited to
FCMO AI and marked ``evidence_image=false``.

Usage::

    visual_desk.py --corpus corpus [--site site] [--dry-run] [--offline] [--now ISO]
    visual_desk.py --render-explainers | --check-explainers [--explainers DIR]
    visual_desk.py --release-src release-src --site site [--offline]   # legacy surface

``--corpus`` writes ``<site>/data/media.json``: one row per story id with the
rights receipt and a ``media`` object in the ``stories.v2`` shape. ``--dry-run``
prints the rows instead and writes nothing. The legacy mode keeps the
pre-SSG ``release-src/data/media.json`` surface alive until the cut-over, under
the same image-level rights rules.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import ipaddress
import json
import math
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
BASE_PATH = "/FCMO-AI-Newsletter/"
ID_RE = re.compile(r"^FCMO-[0-9A-F]{12}$")
BEATS = ("technology", "business", "policy", "society", "research")
LOCALES = ("en", "es-419", "zh-Hans")

EXPLAINER_DIR = Path("site-src/assets/explainers")
EXPLAINER_PREFIX = "assets/explainers/"
EXPLAINER_VARIANTS = 4
EXPLAINER_W, EXPLAINER_H = 1200, 630
EXPLAINER_MAX_BYTES = 12_000
MEDIA_PREFIX = "media/"
MEDIA_FILE_RE = re.compile(r"^FCMO-[0-9A-F]{12}-[0-9a-f]{12}\.(?:jpg|png|webp)$")

# The licence URL must itself be a permissive declaration. NC and ND are refused:
# NC does not fit a publication that may carry sponsorship, and ND forbids the
# crop and resize every hero needs.
PERMISSIVE_LICENSE = re.compile(
    r"https?://creativecommons\.org/(?:licenses/(?:by|by-sa)/(?:[0-9.]+/)?|publicdomain/(?:zero|mark)/(?:[0-9.]+/)?)",
    re.I,
)
ANY_CC = re.compile(r"creativecommons\.org/(?:licenses|publicdomain)/", re.I)
IMAGE_LEVEL_BASES = ("COMMONS_FILE_METADATA", "JSONLD_IMAGEOBJECT_LICENSE")

FCMO_CREDIT = "FCMO AI"
FCMO_LICENSE = "CC BY 4.0"
FCMO_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

MAX_SOURCES = 4
MAX_PAGE_BYTES = 1_500_000
MAX_IMAGE_BYTES = 8_000_000
ICON_MAX_W, ICON_MAX_H = 400, 200
MIN_W, MIN_H = 800, 420
MIN_ASPECT, MAX_ASPECT = 1.25, 2.6
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "FCMO-AI-Newsletter-VisualDesk/2.0 (+https://fcmo-ai.github.io/FCMO-AI-Newsletter/)"

# --- site chrome -----------------------------------------------------------------

# Path tokens that name a site's own furniture rather than a story picture.
CHROME_TOKENS = frozenset(
    {
        "logo", "logos", "logotype", "favicon", "icon", "icons", "sprite", "sprites",
        "wordmark", "lockup", "masthead", "badge", "seal", "avatar", "avatars",
        "placeholder", "default", "fallback", "opengraph", "og", "share", "sharing",
        "social", "brand", "branding", "banner", "emblem", "watermark",
    }
)
CHROME_COMPOUND = re.compile(
    r"(?:twitter|facebook|fb|linkedin)[-_]?(?:card|image|img|preview|thumb|share)|apple-touch|site[-_]?image|share[-_]?image|preview[-_]?card",
    re.I,
)
# Hosts whose images are generated share cards or profile art, never story pictures.
CHROME_HOSTS = frozenset(
    {
        "opengraph.githubassets.com",
        "repository-images.githubusercontent.com",
        "avatars.githubusercontent.com",
        "github.githubassets.com",
        "cdn-thumbnails.huggingface.co",
        "static.arxiv.org",
        "og-image.vercel.app",
    }
)
CHROME_ALT = re.compile(r"\b(?:logo|logotype|icon|wordmark|brand(?:ing)?|avatar|emblem|seal)\b", re.I)
# JSON-LD image objects under these keys describe the publisher, not the story.
NON_STORY_KEYS = frozenset({"logo", "publisher", "brand", "author", "creator", "sourceOrganization", "provider"})


def chrome_reason(image_url: str, alt: str = "") -> str | None:
    """Return a SITE_CHROME code when the URL or alt text marks site furniture."""
    parts = urllib.parse.urlsplit(image_url)
    host = (parts.hostname or "").lower()
    if host in CHROME_HOSTS or host.endswith(".githubassets.com"):
        return "SITE_CHROME:GENERATED_CARD"
    path = urllib.parse.unquote(parts.path).lower()
    if host.endswith("huggingface.co") and "/thumbnails/" in path:
        return "SITE_CHROME:GENERATED_CARD"
    tokens = set(re.split(r"[^a-z0-9]+", path))
    if tokens & CHROME_TOKENS or CHROME_COMPOUND.search(path):
        return "SITE_CHROME:LOGO_PATH"
    if alt and CHROME_ALT.search(alt):
        return "SITE_CHROME:LOGO_ALT"
    return None


def normalized_image_key(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return f"{(parts.hostname or '').lower()}{parts.path}"


# --- network ---------------------------------------------------------------------


class FetchError(Exception):
    """A fetch failed; ``code`` is a public reason code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass
class Response:
    url: str
    content_type: str
    body: bytes


def url_refusal(url: str, allow_private: bool = False) -> str | None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return "URL:UNSUPPORTED"
    if allow_private:
        return None
    host = parts.hostname.lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".lan")):
        return "URL:NON_PUBLIC_HOST"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return None
    if not address.is_global:
        return "URL:NON_PUBLIC_HOST"
    return None


class _CheckedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allow_private: bool) -> None:
        super().__init__()
        self.allow_private = allow_private

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib hook
        refusal = url_refusal(newurl, self.allow_private)
        if refusal:
            raise FetchError(refusal)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    """Polite public-web reader: public hosts only, size caps, per-host spacing, cache."""

    def __init__(self, *, timeout: float = 10.0, min_interval: float = 1.0, allow_private: bool = False) -> None:
        self.timeout = timeout
        self.min_interval = min_interval
        self.allow_private = allow_private
        self._opener = urllib.request.build_opener(_CheckedRedirect(allow_private))
        self._last: dict[str, float] = {}
        self._cache: dict[str, Response | FetchError] = {}

    def get(self, url: str, *, max_bytes: int, html_only: bool = False) -> Response:
        """GET ``url``. ``html_only`` refuses other content types before reading the body."""
        cached = self._cache.get(url)
        if isinstance(cached, FetchError):
            raise cached
        if cached is not None:
            return cached
        try:
            response = self._get(url, max_bytes, html_only)
        except FetchError as exc:
            self._cache[url] = exc
            raise
        self._cache[url] = response
        return response

    def _get(self, url: str, max_bytes: int, html_only: bool) -> Response:
        refusal = url_refusal(url, self.allow_private)
        if refusal:
            raise FetchError(refusal)
        host = (urllib.parse.urlsplit(url).hostname or "").lower()
        wait = self._last.get(host, 0.0) + self.min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                content_type = response.headers.get("content-type", "")
                if html_only and "html" not in content_type.lower():
                    raise FetchError("NOT_HTML")
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise FetchError("FETCH_FAILED:TOO_LARGE")
                return Response(response.geturl(), content_type, body)
        except FetchError:
            raise
        except urllib.error.HTTPError as exc:
            raise FetchError(f"FETCH_FAILED:HTTP_{exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise FetchError(f"FETCH_FAILED:{type(exc).__name__.upper()}") from None
        finally:
            self._last[host] = time.monotonic()


# --- page parsing ------------------------------------------------------------------


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: list[tuple[str, str]] = []
        self.license_links: list[str] = []
        self.ldjson: list[str] = []
        self._in_ld = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): (value or "") for key, value in attrs}
        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").strip().lower()
            if key:
                self.meta.append((key, values.get("content", "").strip()))
        elif tag in ("a", "link"):
            if "license" in values.get("rel", "").lower().split() and values.get("href"):
                self.license_links.append(values["href"].strip())
        elif tag == "script" and values.get("type", "").strip().lower() == "application/ld+json":
            self._in_ld = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_ld:
            self.ldjson.append("".join(self._buf))
            self._in_ld = False

    def handle_data(self, data: str) -> None:
        if self._in_ld:
            self._buf.append(data)


@dataclass
class Candidate:
    image_url: str
    page_url: str
    origin: str  # "jsonld" or "meta"
    alt: str = ""
    license_url: str = ""
    credit: str = ""
    acquire_page: str = ""


@dataclass
class Page:
    url: str
    candidates: list[Candidate] = field(default_factory=list)
    page_license: bool = False


def _clean_text(value: Any, limit: int = 160) -> str:
    if isinstance(value, list):
        value = ", ".join(_clean_text(item, limit) for item in value if _clean_text(item, limit))
    elif isinstance(value, dict):
        value = value.get("name") or value.get("@value") or ""
    text = re.sub(r"<[^>]+>", " ", html.unescape(str(value or "")))
    text = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].rstrip()


def _license_value(value: Any) -> str:
    if isinstance(value, list):
        for item in value:
            found = _license_value(item)
            if found:
                return found
        return ""
    if isinstance(value, dict):
        return str(value.get("@id") or value.get("url") or "").strip()
    return str(value or "").strip()


def _walk_image_objects(node: Any, parent_key: str, out: list[dict[str, Any]]) -> None:
    if parent_key in NON_STORY_KEYS:
        return
    if isinstance(node, list):
        for item in node:
            _walk_image_objects(item, parent_key, out)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("@type")
    kinds = kind if isinstance(kind, list) else [kind]
    if "ImageObject" in kinds:
        out.append(node)
    for key, value in node.items():
        if isinstance(value, (dict, list)):
            _walk_image_objects(value, key, out)


def parse_page(response: Response) -> Page:
    text = response.body.decode("utf-8", errors="replace")
    parser = _PageParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception:  # noqa: BLE001 - malformed HTML only reduces what we can see
        pass
    base = response.url
    page = Page(url=base)
    page.page_license = bool(ANY_CC.search(text)) or any(ANY_CC.search(link) for link in parser.license_links)

    seen: set[str] = set()
    objects: list[dict[str, Any]] = []
    for block in parser.ldjson:
        try:
            _walk_image_objects(json.loads(block), "", objects)
        except (json.JSONDecodeError, RecursionError):
            continue
    for obj in objects:
        raw = obj.get("contentUrl") or obj.get("url")
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        if not isinstance(raw, str) or not raw.strip():
            continue
        image_url = urllib.parse.urljoin(base, raw.strip())
        credit = _clean_text(obj.get("creditText")) or _clean_text(obj.get("creator")) or _clean_text(
            obj.get("author")
        ) or _clean_text(obj.get("copyrightHolder"))
        key = normalized_image_key(image_url)
        if key in seen:
            continue
        seen.add(key)
        page.candidates.append(
            Candidate(
                image_url=image_url,
                page_url=base,
                origin="jsonld",
                alt=_clean_text(obj.get("caption") or obj.get("name") or obj.get("description"), 300),
                license_url=_license_value(obj.get("license")),
                credit=credit,
                acquire_page=_license_value(obj.get("acquireLicensePage")),
            )
        )

    alt = ""
    for key, value in parser.meta:
        if key in ("og:image:alt", "twitter:image:alt") and value and not alt:
            alt = value
    for key, value in parser.meta:
        if key in ("og:image", "og:image:url", "og:image:secure_url", "twitter:image", "twitter:image:src") and value:
            image_url = urllib.parse.urljoin(base, html.unescape(value))
            norm = normalized_image_key(image_url)
            if norm in seen:
                continue
            seen.add(norm)
            page.candidates.append(Candidate(image_url=image_url, page_url=base, origin="meta", alt=alt))
    return page


# --- image-level licence evidence --------------------------------------------------


def commons_file_name(url: str) -> str | None:
    """File name of a Wikimedia Commons file from its upload or file-page URL."""
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    segments = [urllib.parse.unquote(seg) for seg in parts.path.split("/") if seg]
    if host == "upload.wikimedia.org" and len(segments) >= 5 and segments[:2] == ["wikipedia", "commons"]:
        if segments[2] == "thumb" and len(segments) >= 6:
            return segments[5]
        return segments[4]
    if host == "commons.wikimedia.org" and len(segments) >= 2 and segments[0] == "wiki" and segments[1].startswith("File:"):
        return "/".join(segments[1:])[len("File:"):]
    return None


def license_short_name(url: str) -> str:
    match = re.search(r"creativecommons\.org/(licenses|publicdomain)/([a-z-]+)/(?:([0-9.]+)/?)?", url, re.I)
    if not match:
        return ""
    family, kind, version = match.group(1).lower(), match.group(2).lower(), match.group(3) or ""
    if family == "publicdomain":
        return f"CC0 {version or '1.0'}" if kind == "zero" else f"Public Domain Mark {version or '1.0'}"
    return f"CC {kind.upper()} {version}".strip()


@dataclass
class Evidence:
    basis: str
    license_url: str
    license: str
    credit: str
    source_url: str
    download_url: str


def commons_evidence(name: str, fetcher: Any) -> Evidence | str:
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": "1600",
            "titles": f"File:{name}",
        }
    )
    try:
        response = fetcher.get(f"{COMMONS_API}?{query}", max_bytes=600_000)
        data = json.loads(response.body.decode("utf-8", errors="replace"))
        info = data["query"]["pages"][0]["imageinfo"][0]
    except FetchError as exc:
        return exc.code
    except (KeyError, IndexError, TypeError, ValueError):
        return "LICENSE:COMMONS_METADATA_MISSING"
    meta = info.get("extmetadata") or {}

    def value(key: str) -> str:
        entry = meta.get(key)
        return str(entry.get("value") if isinstance(entry, dict) else entry or "").strip()

    if value("NonFree").lower() in ("true", "1", "yes"):
        return "LICENSE:NOT_PERMISSIVE"
    license_url = value("LicenseUrl")
    if license_url.startswith("//"):
        license_url = "https:" + license_url
    if not license_url and value("License").lower() == "cc0":
        license_url = "https://creativecommons.org/publicdomain/zero/1.0/"
    if not PERMISSIVE_LICENSE.match(license_url):
        return "LICENSE:NOT_PERMISSIVE"
    if value("Restrictions"):
        return "LICENSE:RESTRICTED"
    artist = _clean_text(value("Artist"), 120) or _clean_text(value("Credit"), 120)
    if not artist:
        return "LICENSE:NO_CREDIT"
    short = _clean_text(value("LicenseShortName"), 40) or license_short_name(license_url)
    source = str(info.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(name)}")
    download = str(info.get("thumburl") or info.get("url") or "")
    if not download:
        return "LICENSE:COMMONS_METADATA_MISSING"
    return Evidence(
        basis="COMMONS_FILE_METADATA",
        license_url=license_url,
        license=short,
        credit=f"{artist} / Wikimedia Commons",
        source_url=source,
        download_url=download,
    )


def jsonld_evidence(candidate: Candidate) -> Evidence | str:
    if not PERMISSIVE_LICENSE.match(candidate.license_url):
        return "LICENSE:NOT_PERMISSIVE"
    if not candidate.credit:
        return "LICENSE:NO_CREDIT"
    source = candidate.acquire_page if url_refusal(candidate.acquire_page) is None else candidate.page_url
    return Evidence(
        basis="JSONLD_IMAGEOBJECT_LICENSE",
        license_url=candidate.license_url,
        license=license_short_name(candidate.license_url),
        credit=candidate.credit,
        source_url=source,
        download_url=candidate.image_url,
    )


# --- image inspection --------------------------------------------------------------


def image_info(data: bytes) -> tuple[str, int, int] | None:
    """(extension, width, height) for PNG, JPEG or WebP bytes; None otherwise."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR" and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return "png", width, height
    if data[:3] == b"\xff\xd8\xff":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker == 0xFF:
                i += 1
                continue
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height, width = struct.unpack(">HH", data[i + 5 : i + 9])
                return "jpg", width, height
            (length,) = struct.unpack(">H", data[i + 2 : i + 4])
            i += 2 + length
        return None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8 ":
            width, height = struct.unpack("<HH", data[26:30])
            return "webp", width & 0x3FFF, height & 0x3FFF
        if chunk == b"VP8L":
            (bits,) = struct.unpack("<I", data[21:25])
            return "webp", (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return "webp", width, height
    return None


def pixel_refusal(width: int, height: int) -> str | None:
    if width <= ICON_MAX_W or height <= ICON_MAX_H:
        return "SITE_CHROME:ICON_SIZE"
    if width < MIN_W or height < MIN_H:
        return "IMAGE:TOO_SMALL"
    aspect = width / height
    if aspect < MIN_ASPECT:
        return "SITE_CHROME:SQUARE_MARK" if aspect >= 0.8 else "IMAGE:NOT_LANDSCAPE"
    if aspect > MAX_ASPECT:
        return "IMAGE:BANNER_SHAPE"
    return None


# --- beats, alt text and explainers --------------------------------------------------

BEAT_LABELS = {
    "en": {
        "technology": "Technology",
        "business": "Business and economy",
        "policy": "Policy and regulation",
        "society": "Safety and society",
        "research": "Research",
    },
    "es-419": {
        "technology": "Tecnología",
        "business": "Economía y negocios",
        "policy": "Política y regulación",
        "society": "Seguridad y sociedad",
        "research": "Investigación",
    },
    "zh-Hans": {
        "technology": "技术",
        "business": "经济与商业",
        "policy": "政策与监管",
        "society": "安全与社会",
        "research": "研究",
    },
}
EXPLAINER_ALT = {
    "en": "FCMO AI illustration for the {beat} section (original graphic, not source evidence)",
    "es-419": "Ilustración de FCMO AI para la sección {beat} (gráfico original, no es evidencia de la fuente)",
    "zh-Hans": "FCMO AI 为「{beat}」栏目绘制的插图（原创图形，并非来源证据）",
}
LICENSED_ALT = {
    "en": "Illustrative image from a cited source. Credit: {credit}",
    "es-419": "Imagen ilustrativa de una fuente citada. Crédito: {credit}",
    "zh-Hans": "引用来源的示意图片。署名：{credit}",
}

# Fallback beat hints, applied to ``development_type`` first and the primary desk
# second. WP-A2's taxonomy (``beat_for``) wins whenever it is present.
_TYPE_HINTS = (
    ("policy", ("policy", "regulat", "legislat", "government", "export_control", "legal")),
    ("business", ("industry", "transaction", "organizational", "funding", "earnings", "acquisition", "investment", "market")),
    ("society", ("society", "societal", "labor", "labour", "education", "health", "misuse", "election", "incident")),
    ("technology", ("model", "release", "hardware", "infrastructure", "compute", "product")),
    ("research", ("paper", "report", "dataset", "benchmark", "case_study", "evaluation", "science")),
)
_DESK_BEATS = (
    ("policy", ("policy", "geopolit")),
    ("business", ("labs_industry", "industry")),
    ("research", ("evaluation_science", "interpretability", "reasoning_posttraining", "agents_memory", "world_models")),
)


def resolve_beat(record: dict[str, Any]) -> str:
    """The record's beat: record.v3 ``beat``, else the taxonomy module, else hints."""
    beat = record.get("beat")
    if beat in BEATS:
        return str(beat)
    found = _taxonomy_beat(record)
    if found in BEATS:
        return str(found)
    kind = str(record.get("development_type") or "").lower()
    for beat_name, hints in _TYPE_HINTS:
        if any(hint in kind for hint in hints):
            return beat_name
    desk = str(record.get("primary_desk") or "").lower()
    for beat_name, hints in _DESK_BEATS:
        if any(hint in desk for hint in hints):
            return beat_name
    return "technology"


_TAXONOMY: list[Any] = []


def _taxonomy_beat(record: dict[str, Any]) -> str | None:
    """Use ``tools/taxonomy.py`` (WP-A2) when it offers ``beat_for(record)``."""
    if not _TAXONOMY:
        module = None
        path = Path(__file__).resolve().with_name("taxonomy.py")
        if path.is_file():
            try:
                spec = importlib.util.spec_from_file_location("_fcmo_taxonomy", path)
                module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
                spec.loader.exec_module(module)  # type: ignore[union-attr]
            except Exception:  # noqa: BLE001 - a broken module means "no answer"
                module = None
        _TAXONOMY.append(getattr(module, "beat_for", None))
    beat_for = _TAXONOMY[0]
    if not callable(beat_for):
        return None
    try:
        return beat_for(record)
    except Exception:  # noqa: BLE001
        return None


def explainer_name(beat: str, variant: int) -> str:
    return f"{beat}.svg" if variant == 1 else f"{beat}-{variant}.svg"


def explainer_for(story_id: str, beat: str) -> str:
    """Deterministic variant per story, so neighbours on a page rarely repeat."""
    variant = int(hashlib.sha256(story_id.encode("utf-8")).hexdigest(), 16) % EXPLAINER_VARIANTS + 1
    return EXPLAINER_PREFIX + explainer_name(beat, variant)


class _Rand:
    """Hash-based PRNG: identical output on every Python version and platform."""

    def __init__(self, seed: str) -> None:
        self.seed = seed
        self.n = 0

    def random(self) -> float:
        digest = hashlib.sha256(f"{self.seed}:{self.n}".encode("utf-8")).digest()
        self.n += 1
        return int.from_bytes(digest[:7], "big") / float(1 << 56)

    def uniform(self, low: float, high: float) -> float:
        return low + (high - low) * self.random()

    def randint(self, low: int, high: int) -> int:
        return low + min(int(self.random() * (high - low + 1)), high - low)


def _n(value: float) -> str:
    text = f"{value:.1f}"
    if text.endswith(".0"):
        text = text[:-2]
    return "0" if text == "-0" else text


ORANGE = "#FD5204"
INK = "#0B0B0C"
PANEL = "#151518"


def _technology(rng: _Rand) -> list[str]:
    cols, rows, x0, y0, step = 15, 7, 110, 100, 70
    out = [
        f'<pattern id="p" x="{x0 - 3}" y="{y0 - 3}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
        '<circle cx="3" cy="3" r="2.5" fill="#FFFFFF" fill-opacity=".2"/></pattern>',
        f'<rect x="{x0 - 3}" y="{y0 - 3}" width="{(cols - 1) * step + 6}" height="{(rows - 1) * step + 6}" fill="url(#p)"/>',
    ]
    chip_c, chip_r = rng.randint(4, cols - 7), rng.randint(1, rows - 4)
    walks: list[tuple[list[tuple[float, float]], bool]] = []
    for index in range(10):
        c, r = rng.randint(0, cols - 1), rng.randint(0, rows - 1)
        direction = 1 if c < cols / 2 else -1
        points = [(x0 + c * step, y0 + r * step)]
        for _ in range(rng.randint(3, 7)):
            if rng.random() < 0.3:
                r = min(rows - 1, max(0, r + (1 if rng.random() < 0.5 else -1)))
            else:
                c = min(cols - 1, max(0, c + direction))
            point = (x0 + c * step, y0 + r * step)
            if point != points[-1]:
                points.append(point)
        if len(points) > 1:
            walks.append((points, index < 2))
    for points, hot in walks:
        colour, width = (ORANGE, 5) if hot else ("#FFFFFF", 3)
        opacity = "1" if hot else ".3"
        path = " ".join(f"{_n(x)},{_n(y)}" for x, y in points)
        out.append(
            f'<polyline points="{path}" fill="none" stroke="{colour}" stroke-opacity="{opacity}" '
            f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        ex, ey = points[-1]
        out.append(
            f'<circle cx="{_n(ex)}" cy="{_n(ey)}" r="{8 if hot else 6}" fill="{INK}" stroke="{colour}" '
            f'stroke-opacity="{opacity}" stroke-width="3"/>'
        )
    cx, cy = x0 + chip_c * step - 35, y0 + chip_r * step - 35
    size = 2 * step + 70
    pins = []
    for k in range(6):
        px = cx + 25 + k * (size - 50) / 5
        pins.append(f"M{_n(px)} {cy - 18}V{cy}M{_n(px)} {cy + size}V{cy + size + 18}")
        py = cy + 25 + k * (size - 50) / 5
        pins.append(f"M{cx - 18} {_n(py)}H{cx}M{cx + size} {_n(py)}H{cx + size + 18}")
    out.append(f'<path d="{"".join(pins)}" stroke="{ORANGE}" stroke-width="4" stroke-linecap="round"/>')
    out.append(f'<rect x="{cx}" y="{cy}" width="{size}" height="{size}" rx="16" fill="{PANEL}" stroke="{ORANGE}" stroke-width="4"/>')
    inner = size - 90
    out.append(
        f'<rect x="{cx + 45}" y="{cy + 45}" width="{inner}" height="{inner}" rx="8" fill="{ORANGE}" fill-opacity=".9"/>'
    )
    return out


def _business(rng: _Rand) -> list[str]:
    count, left, right, base, top = 13, 130, 1070, 540, 110
    gap = (right - left) / count
    bar = gap * 0.62
    out = [
        "".join(
            f'<line x1="{left - 30}" y1="{_n(y)}" x2="{right + 20}" y2="{_n(y)}" stroke="#FFFFFF" stroke-opacity=".07" stroke-width="2"/>'
            for y in (base - 105, base - 210, base - 315, base - 420)
        )
    ]
    value = rng.uniform(0.16, 0.28)
    dip = rng.randint(3, 8)
    values = []
    for index in range(count):
        drift = rng.uniform(-0.03, 0.09) if index != dip else -rng.uniform(0.08, 0.14)
        value = min(0.96, max(0.1, value + drift))
        values.append(value)
    points = []
    for index, share in enumerate(values):
        height = share * (base - top)
        x = left + index * gap + (gap - bar) / 2
        hot = index >= count - 3
        fill = f'fill="{ORANGE}" fill-opacity=".85"' if hot else 'fill="#FFFFFF" fill-opacity=".13"'
        out.append(f'<rect x="{_n(x)}" y="{_n(base - height)}" width="{_n(bar)}" height="{_n(height)}" rx="4" {fill}/>')
        points.append((x + bar / 2, base - height - 26))
    bench = [(x, y + rng.uniform(40, 90)) for x, y in points]
    out.append(
        f'<polyline points="{" ".join(f"{_n(x)},{_n(y)}" for x, y in bench)}" fill="none" stroke="#FFFFFF" '
        'stroke-opacity=".35" stroke-width="3" stroke-dasharray="10 10"/>'
    )
    out.append(
        f'<polyline points="{" ".join(f"{_n(x)},{_n(y)}" for x, y in points)}" fill="none" stroke="{ORANGE}" '
        'stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    lx, ly = points[-1]
    out.append(f'<circle cx="{_n(lx)}" cy="{_n(ly)}" r="11" fill="{INK}" stroke="{ORANGE}" stroke-width="5"/>')
    out.append(f'<line x1="{left - 30}" y1="{base}" x2="{right + 20}" y2="{base}" stroke="#FFFFFF" stroke-opacity=".4" stroke-width="3"/>')
    return out


def _policy(rng: _Rand) -> list[str]:
    cx, cy, radius0, row_gap, rows, seat = 600, 520, 165, 50, 6, 10
    seats: list[tuple[float, float, float]] = []
    for row in range(rows):
        radius = radius0 + row * row_gap
        count = int(math.pi * radius / 30)
        for k in range(count):
            angle = math.pi * (k + 0.5) / count
            seats.append((angle, cx + radius * math.cos(math.pi - angle), cy - radius * math.sin(angle)))
    seats.sort(key=lambda item: item[0])
    total = len(seats)
    majority = int(total * rng.uniform(0.38, 0.58))
    swing = int(total * rng.uniform(0.08, 0.14))
    groups = (
        (ORANGE, "1", seats[:majority]),
        ("#FFFFFF", ".6", seats[majority : majority + swing]),
        ("#FFFFFF", ".2", seats[majority + swing :]),
    )
    out = []
    for colour, opacity, members in groups:
        dots = "".join(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{seat}"/>' for _, x, y in members)
        out.append(f'<g fill="{colour}" fill-opacity="{opacity}">{dots}</g>')
    width = 2 * (radius0 - 40)
    out.append(
        f'<rect x="{cx - width / 2:.0f}" y="{cy + 22}" width="{width:.0f}" height="10" rx="5" fill="{ORANGE}"/>'
    )
    out.append(
        f'<line x1="{cx - radius0 - rows * row_gap}" y1="{cy + 56}" x2="{cx + radius0 + rows * row_gap}" y2="{cy + 56}" '
        'stroke="#FFFFFF" stroke-opacity=".3" stroke-width="3"/>'
    )
    return out


def _society(rng: _Rand) -> list[str]:
    clusters = rng.randint(3, 4)
    slots = [(250, 230), (560, 400), (880, 220), (1000, 450), (420, 170)]
    hubs = []
    out_edges, out_nodes, out_hubs = [], [], []
    for index in range(clusters):
        bx, by = slots[index]
        hx, hy = bx + rng.uniform(-40, 40), by + rng.uniform(-30, 30)
        hubs.append((hx, hy))
        members = []
        for k in range(rng.randint(7, 10)):
            angle = 2 * math.pi * k / 9 + rng.uniform(-0.3, 0.3)
            dist = rng.uniform(80, 140)
            members.append((hx + dist * math.cos(angle), min(575, max(60, hy + dist * 0.8 * math.sin(angle)))))
        for mx, my in members:
            out_edges.append(f"M{_n(hx)} {_n(hy)}L{_n(mx)} {_n(my)}")
        for (ax, ay), (bx2, by2) in zip(members, members[1:]):
            if rng.random() < 0.5:
                out_edges.append(f"M{_n(ax)} {_n(ay)}L{_n(bx2)} {_n(by2)}")
        for mx, my in members:
            hot = rng.random() < 0.12
            fill = f'fill="{ORANGE}"' if hot else 'fill="#FFFFFF" fill-opacity=".35"'
            out_nodes.append(f'<circle cx="{_n(mx)}" cy="{_n(my)}" r="{_n(rng.uniform(6, 11))}" {fill}/>')
    links = [f"M{_n(ax)} {_n(ay)}L{_n(bx)} {_n(by)}" for (ax, ay), (bx, by) in zip(hubs, hubs[1:])]
    for hx, hy in hubs:
        out_hubs.append(
            f'<circle cx="{_n(hx)}" cy="{_n(hy)}" r="34" fill="{INK}" stroke="{ORANGE}" stroke-width="5"/>'
            f'<circle cx="{_n(hx)}" cy="{_n(hy - 9)}" r="9" fill="{ORANGE}"/>'
            f'<path d="M{_n(hx - 16)} {_n(hy + 18)}a16 14 0 0 1 32 0z" fill="{ORANGE}"/>'
        )
    return [
        f'<path d="{"".join(out_edges)}" stroke="#FFFFFF" stroke-opacity=".16" stroke-width="2"/>',
        f'<path d="{"".join(links)}" stroke="{ORANGE}" stroke-opacity=".7" stroke-width="4" stroke-dasharray="4 12" stroke-linecap="round"/>',
        *out_nodes,
        *out_hubs,
    ]


def _research(rng: _Rand, falling: bool = False) -> list[str]:
    left, right, top, base = 130, 1080, 100, 530
    rate = rng.uniform(2.2, 4.5)
    floor = rng.uniform(0.08, 0.18)
    ceiling = rng.uniform(0.78, 0.9)

    def curve(t: float) -> float:
        rise = (ceiling - floor) * (1 - math.exp(-rate * t))
        return ceiling - rise if falling else floor + rise

    def xy(t: float, v: float) -> tuple[float, float]:
        return left + t * (right - left), base - v * (base - top)

    steps = [k / 40 for k in range(41)]
    upper = [xy(t, curve(t) + 0.05 + 0.06 * t) for t in steps]
    lower = [xy(t, curve(t) - 0.05 - 0.06 * t) for t in reversed(steps)]
    band = " ".join(f"{_n(x)},{_n(y)}" for x, y in upper + lower)
    line = " ".join(f"{_n(x)},{_n(y)}" for x, y in (xy(t, curve(t)) for t in steps))
    ticks = "".join(f"M{_n(left + k * (right - left) / 8)} {base}v14" for k in range(1, 9))
    ticks += "".join(f"M{left} {_n(base - k * (base - top) / 5)}h-14" for k in range(1, 6))
    out = [
        f'<path d="M{left} {top - 20}V{base}H{right + 20}{ticks}" fill="none" stroke="#FFFFFF" stroke-opacity=".35" stroke-width="3"/>',
        f'<polygon points="{band}" fill="{ORANGE}" fill-opacity=".13"/>',
    ]
    dots, hot = [], []
    for k in range(44):
        t = rng.uniform(0.02, 0.98)
        v = curve(t) + rng.uniform(-0.1, 0.1)
        x, y = xy(t, v)
        if k % 11 == 0:
            hot.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="8" fill="{INK}" stroke="{ORANGE}" stroke-width="4"/>')
        else:
            dots.append(f'<circle cx="{_n(x)}" cy="{_n(y)}" r="5"/>')
    out.append(f'<g fill="#FFFFFF" fill-opacity=".5">{"".join(dots)}</g>')
    out.append(
        f'<polyline points="{line}" fill="none" stroke="{ORANGE}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>'
    )
    out.extend(hot)
    return out


MOTIFS: dict[str, Callable[[_Rand], list[str]]] = {
    "technology": _technology,
    "business": _business,
    "policy": _policy,
    "society": _society,
    "research": _research,
}


def render_explainer(beat: str, variant: int) -> str:
    """Language-neutral FCMO explainer art: no words, so no locale ever leaks."""
    rng = _Rand(f"fcmo-explainer:{beat}:{variant}")
    # Even variants mirror the composition; a chart keeps its axis on the left and
    # changes the curve direction instead.
    mirror = variant % 2 == 0 and beat not in ("business", "research")
    gx = rng.uniform(80, 440) if variant % 2 == 0 else rng.uniform(760, 1120)
    gy = rng.uniform(40, 200)
    motif = MOTIFS[beat]
    body = "".join(_research(rng, falling=variant % 2 == 0) if beat == "research" else motif(rng))
    if mirror:
        body = f'<g transform="matrix(-1 0 0 1 {EXPLAINER_W} 0)">{body}</g>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {EXPLAINER_W} {EXPLAINER_H}" '
        f'width="{EXPLAINER_W}" height="{EXPLAINER_H}">'
        '<defs><radialGradient id="g"><stop offset="0" stop-color="#FD5204" stop-opacity=".28"/>'
        '<stop offset="1" stop-color="#FD5204" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{EXPLAINER_W}" height="{EXPLAINER_H}" fill="{INK}"/>'
        f'<circle cx="{_n(gx)}" cy="{_n(gy)}" r="380" fill="url(#g)"/>'
        f"{body}"
        f'<rect x="80" y="596" width="96" height="6" fill="{ORANGE}"/>'
        "</svg>\n"
    )


def explainer_files() -> dict[str, str]:
    return {
        explainer_name(beat, variant): render_explainer(beat, variant)
        for beat in BEATS
        for variant in range(1, EXPLAINER_VARIANTS + 1)
    }


def write_explainers(directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    files = explainer_files()
    for name, svg in files.items():
        (directory / name).write_text(svg, encoding="utf-8")
    return len(files)


def check_explainers(directory: Path) -> list[str]:
    problems = []
    for name, svg in explainer_files().items():
        path = directory / name
        if not path.is_file():
            problems.append(f"{name}: missing")
        elif path.read_text(encoding="utf-8") != svg:
            problems.append(f"{name}: differs from the generator")
    return problems


# --- rows ---------------------------------------------------------------------------


def explainer_row(story_id: str, beat: str, rejected: list[dict[str, str]]) -> dict[str, Any]:
    local_path = explainer_for(story_id, beat)
    label = {locale: BEAT_LABELS[locale][beat] for locale in LOCALES}
    alt = {locale: EXPLAINER_ALT[locale].format(beat=label[locale]) for locale in LOCALES}
    row: dict[str, Any] = {
        "id": story_id,
        "mode": "fcmo_explainer",
        "sourced": False,
        "generated": True,
        "rights_state": "FCMO_OWNED",
        "evidence_image": False,
        "beat": beat,
        "local_path": local_path,
        "image_url": BASE_PATH + local_path,
        "width": EXPLAINER_W,
        "height": EXPLAINER_H,
        "credit": FCMO_CREDIT,
        "license": FCMO_LICENSE,
        "license_url": FCMO_LICENSE_URL,
        "reuse_basis": "original FCMO AI graphic",
        "fit": "cover",
        "reason": "NO_RIGHTS_PROVEN_SOURCE_IMAGE",
        "alt": alt,
    }
    if rejected:
        row["rejected_candidates"] = rejected
    row["media"] = contract_media(row)
    return row


def licensed_row(
    story_id: str,
    beat: str,
    evidence: Evidence,
    candidate: Candidate,
    blob: bytes,
    ext: str,
    width: int,
    height: int,
    now: str,
    rejected: list[dict[str, str]],
) -> dict[str, Any]:
    digest = hashlib.sha256(blob).hexdigest()
    local_path = f"{MEDIA_PREFIX}{story_id}-{digest[:12]}.{ext}"
    alt = {locale: LICENSED_ALT[locale].format(credit=evidence.credit) for locale in LOCALES}
    row: dict[str, Any] = {
        "id": story_id,
        "mode": "licensed_source",
        "sourced": True,
        "generated": False,
        "rights_state": "PERMISSIVE_LICENSE",
        "evidence_image": False,
        "beat": beat,
        "local_path": local_path,
        "image_url": BASE_PATH + local_path,
        "width": width,
        "height": height,
        "bytes": len(blob),
        "sha256": digest,
        "credit": evidence.credit,
        "license": evidence.license or license_short_name(evidence.license_url),
        "license_url": evidence.license_url,
        "rights_basis": evidence.basis,
        "reuse_basis": "image-level permissive licence: " + evidence.basis,
        "source_url": evidence.source_url,
        "source_page": candidate.page_url,
        "image_origin_url": candidate.image_url,
        "checked_at": now,
        "fit": "cover",
        "alt": alt,
    }
    if rejected:
        row["rejected_candidates"] = rejected
    row["media"] = contract_media(row)
    return row


def contract_media(row: dict[str, Any]) -> dict[str, Any]:
    """The ``stories.v2`` ``media`` object for a desk row."""
    media = {
        "kind": "licensed" if row["mode"] == "licensed_source" else "explainer",
        "local_path": row["local_path"],
        "credit": row["credit"],
        "license": row["license"],
        "alt": dict(row["alt"]),
        "width": int(row["width"]),
        "height": int(row["height"]),
    }
    if row["mode"] == "licensed_source":
        media["source_url"] = row["source_url"]
    return media


# --- the desk ---------------------------------------------------------------------------


@dataclass
class Outcome:
    rows: list[dict[str, Any]]
    blobs: dict[str, bytes]  # local_path -> bytes for newly accepted images

    @property
    def licensed(self) -> int:
        return sum(1 for row in self.rows if row["mode"] == "licensed_source")

    @property
    def explainers(self) -> int:
        return sum(1 for row in self.rows if row["mode"] == "fcmo_explainer")


def carried_licensed_row(previous: dict[str, Any], site: Path) -> bool:
    """A previous licensed row survives only if it still passes today's rules."""
    if previous.get("mode") != "licensed_source" or previous.get("rights_basis") not in IMAGE_LEVEL_BASES:
        return False
    return not _licensed_errors(previous, site, check_files=True)


def resolve_media(
    records: list[dict[str, Any]],
    *,
    site: Path,
    previous: dict[str, dict[str, Any]],
    fetcher: Any | None,
    now: str,
    max_sources: int = MAX_SOURCES,
    explainer: Callable[[str, str, list[dict[str, str]]], dict[str, Any]] = explainer_row,
) -> Outcome:
    """Decide one media row per record. ``fetcher=None`` means offline."""
    rows: list[dict[str, Any]] = []
    blobs: dict[str, bytes] = {}
    pending: list[tuple[int, dict[str, Any], str]] = []
    for record in records:
        story_id = str(record["id"])
        beat = resolve_beat(record)
        old = previous.get(story_id) or {}
        if carried_licensed_row(old, site):
            row = dict(old)
            row["beat"] = beat
            row["media"] = contract_media(row)
            rows.append(row)
        else:
            pending.append((len(rows), record, beat))
            rows.append({})

    pages: dict[str, Page | str] = {}
    if fetcher is not None:
        for _, record, _ in pending:
            for source in _sources(record, max_sources):
                if source in pages:
                    continue
                refusal = url_refusal(source, getattr(fetcher, "allow_private", False))
                if refusal:
                    pages[source] = refusal
                    continue
                try:
                    response = fetcher.get(source, max_bytes=MAX_PAGE_BYTES, html_only=True)
                except FetchError as exc:
                    pages[source] = exc.code
                    continue
                if "html" not in response.content_type.lower():
                    pages[source] = "NOT_HTML"
                    continue
                pages[source] = parse_page(response)

    # An image referenced by two or more different pages is the site's own art.
    referenced: dict[str, set[str]] = {}
    for page in pages.values():
        if isinstance(page, Page):
            for candidate in page.candidates:
                referenced.setdefault(normalized_image_key(candidate.image_url), set()).add(page.url)
    repeated = {key for key, urls in referenced.items() if len(urls) >= 2}
    used_digests = {str(row.get("sha256")) for row in rows if row.get("sha256")}

    for slot, record, beat in pending:
        story_id = str(record["id"])
        rejected: list[dict[str, str]] = []
        chosen: dict[str, Any] | None = None
        for source in _sources(record, max_sources) if fetcher is not None else []:
            page = pages.get(source)
            if not isinstance(page, Page):
                rejected.append({"source": source, "reason": str(page or "FETCH_FAILED:UNKNOWN")})
                continue
            if not page.candidates:
                rejected.append({"source": source, "reason": "NO_IMAGE"})
                continue
            ordered = sorted(page.candidates, key=lambda c: 0 if c.origin == "jsonld" else 1)
            for candidate in ordered:
                verdict = _evaluate(candidate, page, fetcher, repeated, used_digests)
                if isinstance(verdict, str):
                    rejected.append({"source": source, "reason": verdict})
                    continue
                evidence, blob, ext, width, height = verdict
                chosen = licensed_row(story_id, beat, evidence, candidate, blob, ext, width, height, now, _dedupe(rejected))
                blobs[chosen["local_path"]] = blob
                used_digests.add(chosen["sha256"])
                break
            if chosen:
                break
        rows[slot] = chosen or explainer(story_id, beat, _dedupe(rejected))
    return Outcome(rows=rows, blobs=blobs)


def _sources(record: dict[str, Any], limit: int) -> list[str]:
    urls = []
    for url in record.get("source_urls") or []:
        if isinstance(url, str) and url.strip() and url.strip() not in urls:
            urls.append(url.strip())
    return urls[:limit]


def _dedupe(rejected: list[dict[str, str]]) -> list[dict[str, str]]:
    seen, out = set(), []
    for item in rejected:
        key = (item["source"], item["reason"])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _evaluate(
    candidate: Candidate,
    page: Page,
    fetcher: Any,
    repeated: set[str],
    used_digests: set[str],
) -> tuple[Evidence, bytes, str, int, int] | str:
    refusal = url_refusal(candidate.image_url, getattr(fetcher, "allow_private", False))
    if refusal:
        return refusal
    chrome = chrome_reason(candidate.image_url, candidate.alt)
    if chrome:
        return chrome
    if normalized_image_key(candidate.image_url) in repeated:
        return "SITE_CHROME:REPEATED"
    commons = commons_file_name(candidate.image_url)
    if commons:
        evidence = commons_evidence(commons, fetcher)
    elif candidate.origin == "jsonld" and candidate.license_url:
        evidence = jsonld_evidence(candidate)
    else:
        return "LICENSE:PAGE_ONLY" if page.page_license else "LICENSE:NONE"
    if isinstance(evidence, str):
        return evidence
    if chrome_reason(evidence.download_url):
        return "SITE_CHROME:LOGO_PATH"
    try:
        response = fetcher.get(evidence.download_url, max_bytes=MAX_IMAGE_BYTES)
    except FetchError as exc:
        return "IMAGE:TOO_LARGE" if exc.code == "FETCH_FAILED:TOO_LARGE" else exc.code
    info = image_info(response.body)
    if info is None:
        return "IMAGE:NOT_RASTER"
    ext, width, height = info
    pixel = pixel_refusal(width, height)
    if pixel:
        return pixel
    if hashlib.sha256(response.body).hexdigest() in used_digests:
        return "IMAGE:DUPLICATE"
    return evidence, response.body, ext, width, height


# --- validation ----------------------------------------------------------------------------


def _licensed_errors(row: dict[str, Any], site: Path, *, check_files: bool) -> list[str]:
    rid = str(row.get("id") or "<missing-id>")
    errors = []
    if row.get("sourced") is not True or row.get("rights_state") != "PERMISSIVE_LICENSE":
        errors.append(f"{rid}: licensed source lacks sourced/rights state")
    license_url = str(row.get("license_url") or "")
    if not PERMISSIVE_LICENSE.match(license_url):
        errors.append(f"{rid}: license_url is not a recognized permissive reuse declaration")
    if row.get("rights_basis") not in IMAGE_LEVEL_BASES:
        errors.append(f"{rid}: rights basis is not an image-level licence (a page licence never licenses its og:image)")
    for key in ("local_path", "credit", "license", "source_url", "sha256"):
        if not str(row.get(key) or "").strip():
            errors.append(f"{rid}: licensed source lacks {key}")
    local_path = str(row.get("local_path") or "")
    if local_path and not (local_path.startswith(MEDIA_PREFIX) and MEDIA_FILE_RE.match(local_path[len(MEDIA_PREFIX):])):
        errors.append(f"{rid}: licensed image must be stored locally under media/ (no hotlinks)")
    origin = str(row.get("image_origin_url") or row.get("image_url") or "")
    if origin and chrome_reason(origin):
        errors.append(f"{rid}: licensed image is site chrome ({chrome_reason(origin)})")
    width, height = row.get("width"), row.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or pixel_refusal(width, height):
        errors.append(f"{rid}: licensed image dimensions are not a landscape hero")
    if check_files and local_path.startswith(MEDIA_PREFIX) and row.get("sha256"):
        path = site / local_path
        if not path.is_file():
            errors.append(f"{rid}: licensed image file is missing from the publication tree")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != row.get("sha256"):
            errors.append(f"{rid}: licensed image file does not match its sha256")
    return errors


def _media_object_errors(row: dict[str, Any]) -> list[str]:
    rid = str(row.get("id") or "<missing-id>")
    media = row.get("media")
    if media is None:
        return []
    if not isinstance(media, dict):
        return [f"{rid}: media must be an object"]
    errors = []
    kind = "licensed" if row.get("mode") == "licensed_source" else "explainer"
    if media.get("kind") != kind:
        errors.append(f"{rid}: media.kind does not match the row mode")
    if media.get("local_path") != row.get("local_path"):
        errors.append(f"{rid}: media.local_path does not match the row")
    if not re.match(r"^(media|assets)/[A-Za-z0-9._/-]+$", str(media.get("local_path") or "")):
        errors.append(f"{rid}: media.local_path is not a publication path")
    if not str(media.get("credit") or "").strip():
        errors.append(f"{rid}: media.credit is empty")
    alt = media.get("alt")
    if not isinstance(alt, dict) or not str(alt.get("en") or "").strip():
        errors.append(f"{rid}: media.alt.en is empty")
    if kind == "licensed" and not str(media.get("source_url") or "").strip():
        errors.append(f"{rid}: licensed media lacks source_url")
    return errors


def validate_media_rows(
    rows: list[dict[str, Any]],
    expected_ids: set[str],
    site: Path,
    explainers: Path | None = None,
    *,
    check_files: bool = True,
) -> None:
    """Prove every published visual has a current, image-level reuse basis."""
    errors: list[str] = []
    ids = [str(row.get("id") or "") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not rid for rid in ids):
        errors.append("every media row must be an object with a non-empty id")
    if len(set(ids)) != len(ids):
        errors.append("duplicate media ids")
    if set(ids) != expected_ids:
        errors.append(
            f"media ids do not match stories: missing={sorted(expected_ids - set(ids))} extra={sorted(set(ids) - expected_ids)}"
        )
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "<missing-id>")
        mode = row.get("mode")
        if mode == "licensed_source":
            errors.extend(_licensed_errors(row, site, check_files=check_files))
        elif mode == "fcmo_explainer":
            if row.get("sourced") is not False or row.get("generated") is not True:
                errors.append(f"{rid}: FCMO explainer provenance flags are inconsistent")
            if row.get("rights_state") != "FCMO_OWNED" or row.get("evidence_image") is not False:
                errors.append(f"{rid}: FCMO explainer rights/evidence state is inconsistent")
            if not str(row.get("credit") or "").strip():
                errors.append(f"{rid}: FCMO explainer lacks credit")
            local_path = str(row.get("local_path") or "")
            legacy_prefix = BASE_PATH + "assets/story-media/"
            image_url = str(row.get("image_url") or "")
            if local_path:
                if not local_path.startswith(EXPLAINER_PREFIX):
                    errors.append(f"{rid}: FCMO explainer must use a local explainer asset")
                elif check_files and explainers is not None and not (explainers / local_path[len(EXPLAINER_PREFIX):]).is_file():
                    errors.append(f"{rid}: FCMO explainer asset is missing")
            elif not image_url.startswith(legacy_prefix):
                errors.append(f"{rid}: FCMO explainer must use a local story-media asset")
            elif check_files and not (site / "assets" / "story-media" / image_url[len(legacy_prefix):]).is_file():
                errors.append(f"{rid}: FCMO explainer asset is missing from the publication tree")
        else:
            errors.append(f"{rid}: unsupported media mode {mode!r}")
            continue
        errors.extend(_media_object_errors(row))
    if errors:
        raise ValueError("media rights gate FAILED: " + "; ".join(errors))


# --- IO ---------------------------------------------------------------------------------------


def resolve_now(value: str | None) -> str:
    raw = value or os.environ.get("FCMO_NOW") or ""
    if raw:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        moment = parsed.astimezone(timezone.utc)
    else:
        moment = datetime.now(timezone.utc)
    return moment.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_corpus_records(corpus: Path) -> list[dict[str, Any]]:
    """Records of ``corpus/data/developments.jsonl`` plus carried-forward ids."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    path = corpus / "data" / "developments.jsonl"
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found")
    lines = path.read_text(encoding="utf-8").splitlines()
    carried = corpus / "carried.jsonl"
    extra = carried.read_text(encoding="utf-8").splitlines() if carried.is_file() else []
    for line, is_carried in [(item, False) for item in lines] + [(item, True) for item in extra]:
        if not line.strip():
            continue
        obj = json.loads(line)
        record = obj.get("record") if is_carried else obj
        if not isinstance(record, dict):
            continue
        story_id = str(record.get("id") or "")
        if ID_RE.match(story_id) and story_id not in seen:
            seen.add(story_id)
            records.append(record)
    return records


def load_previous(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(rows, list):
        return {}
    return {str(row.get("id")): row for row in rows if isinstance(row, dict) and row.get("id")}


def store_blobs(site: Path, blobs: dict[str, bytes]) -> None:
    for local_path, blob in blobs.items():
        target = site / local_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)


def prune_media(site: Path, rows: list[dict[str, Any]]) -> list[str]:
    """Remove desk-named files in ``site/media`` that no row references any more."""
    directory = site / "media"
    if not directory.is_dir():
        return []
    keep = {str(row.get("local_path") or "")[len(MEDIA_PREFIX):] for row in rows if row.get("mode") == "licensed_source"}
    removed = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and MEDIA_FILE_RE.match(path.name) and path.name not in keep:
            path.unlink()
            removed.append(path.name)
    return removed


def run_corpus(args: argparse.Namespace, fetcher: Any | None) -> int:
    records = load_corpus_records(args.corpus)
    out = args.out or (args.site / "data" / "media.json")
    now = resolve_now(args.now)
    outcome = resolve_media(records, site=args.site, previous=load_previous(out), fetcher=fetcher, now=now, max_sources=args.max_sources)
    expected = {str(record["id"]) for record in records}
    summary = f"licensed={outcome.licensed} explainer={outcome.explainers} total={len(outcome.rows)}"
    if args.dry_run:
        validate_media_rows(outcome.rows, expected, args.site, args.explainers, check_files=False)
        json.dump(outcome.rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        print(f"visual desk DRY-RUN {summary} rights=PASS", file=sys.stderr)
        return 0
    store_blobs(args.site, outcome.blobs)
    validate_media_rows(outcome.rows, expected, args.site, args.explainers)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(outcome.rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pruned = prune_media(args.site, outcome.rows)
    print(f"visual desk OK {summary} pruned={len(pruned)} rights=PASS")
    return 0


# --- legacy surface (release-src; retired at the SSG cut-over) -----------------------------


def load_briefs(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        brief = obj.get("brief")
        if isinstance(brief, dict):
            rows.append(brief)
    return rows


def svg_for(brief: dict[str, Any]) -> str:
    """Legacy per-story explainer (release-src surface only)."""
    title = html.escape(str(brief.get("title") or "FCMO AI Research"))
    desk = html.escape(str(brief.get("primary_desk") or "research").replace("_", " ").upper())
    evidence = str(brief.get("evidence_class") or brief.get("evidence") or "").strip()
    importance = str(brief.get("importance_effective_score") or brief.get("importance_score") or "").strip()
    facts = []
    if evidence:
        facts.append(f"EVIDENCE {html.escape(evidence)}")
    if importance:
        facts.append(f"IMPACT {html.escape(importance)}/10")
    fact_line = (
        f'<text x="110" y="790" font-family="Arial,Helvetica,sans-serif" font-size="28" fill="#FFFFFF">{" · ".join(facts)}</text>\n'
        if facts
        else ""
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" role="img" aria-labelledby="t d">
<title id="t">{title}</title>
<desc id="d">FCMO original editorial explainer for {title}.</desc>
<rect width="1600" height="900" fill="#0B0B0C"/>
<circle cx="1320" cy="170" r="310" fill="#FD5204" opacity=".18"/>
<circle cx="1450" cy="780" r="430" fill="#FFFFFF" opacity=".035"/>
<path d="M0 710 C330 560 490 810 790 650 S1260 420 1600 600" fill="none" stroke="#FD5204" stroke-width="16"/>
<text x="110" y="120" font-family="Arial,Helvetica,sans-serif" font-size="34" letter-spacing="8" fill="#FD5204">FCMO AI NEWSLETTER</text>
<text x="110" y="198" font-family="Arial,Helvetica,sans-serif" font-size="25" letter-spacing="5" fill="#B8B8BC">{desk}</text>
<foreignObject x="110" y="270" width="1120" height="330">
  <div xmlns="http://www.w3.org/1999/xhtml" style="font:700 68px/1.08 Arial,Helvetica,sans-serif;color:#fff">{title}</div>
</foreignObject>
{fact_line}<text x="110" y="838" font-family="Arial,Helvetica,sans-serif" font-size="20" fill="#99999F">FCMO original editorial graphic · not source evidence</text>
</svg>"""


def run_legacy(args: argparse.Namespace, fetcher: Any | None) -> int:
    media_path = args.release_src / "data" / "media.json"
    assets = args.site / "assets" / "story-media"
    assets.mkdir(parents=True, exist_ok=True)
    briefs = load_briefs(args.release_src)
    by_id = {str(brief["id"]): brief for brief in briefs}

    def legacy_explainer(story_id: str, beat: str, rejected: list[dict[str, str]]) -> dict[str, Any]:
        asset_rel = f"assets/story-media/{story_id}.svg"
        if not args.dry_run:
            (args.site / asset_rel).write_text(svg_for(by_id[story_id]), encoding="utf-8")
        row: dict[str, Any] = {
            "id": story_id,
            "mode": "fcmo_explainer",
            "sourced": False,
            "generated": True,
            "rights_state": "FCMO_OWNED",
            "image_url": BASE_PATH + asset_rel,
            "credit": "FCMO AI Research Desk",
            "license": "FCMO original editorial graphic",
            "reuse_basis": "original publication-owned artwork",
            "fit": "cover",
            "evidence_image": False,
            "beat": beat,
            "reason": "NO_RIGHTS_PROVEN_SOURCE_IMAGE",
        }
        if rejected:
            row["rejected_candidates"] = rejected
        return row

    now = resolve_now(args.now)
    outcome = resolve_media(
        briefs,
        site=args.site,
        previous=load_previous(media_path),
        fetcher=fetcher,
        now=now,
        max_sources=args.max_sources,
        explainer=legacy_explainer,
    )
    expected = set(by_id)
    if args.dry_run:
        validate_media_rows(outcome.rows, expected, args.site, check_files=False)
        json.dump(outcome.rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    store_blobs(args.site, outcome.blobs)
    # Validation happens before media.json is replaced, so a bad rights receipt
    # cannot partially update the canonical publication state.
    validate_media_rows(outcome.rows, expected, args.site)
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_text(json.dumps(outcome.rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"visual desk OK; licensed={outcome.licensed}; generated={outcome.explainers}; total={len(outcome.rows)}; rights=PASS"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", type=Path, help="corpus directory (data/developments.jsonl)")
    parser.add_argument("--release-src", type=Path, help="legacy release-src tree")
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--explainers", type=Path, default=EXPLAINER_DIR)
    parser.add_argument("--out", type=Path, help="media.json path (default <site>/data/media.json)")
    parser.add_argument("--dry-run", action="store_true", help="print the rows; write nothing")
    parser.add_argument("--offline", action="store_true", help="skip network discovery (explainer fallback)")
    parser.add_argument("--now", help="ISO 8601 time for receipts (else FCMO_NOW, else the clock)")
    parser.add_argument("--max-sources", type=int, default=MAX_SOURCES)
    parser.add_argument("--render-explainers", action="store_true", help="write the explainer SVGs")
    parser.add_argument("--check-explainers", action="store_true", help="exit 1 if the SVGs drifted")
    args = parser.parse_args(argv)

    if args.render_explainers:
        count = write_explainers(args.explainers)
        print(f"explainers written={count} dir={args.explainers}")
        return 0
    if args.check_explainers:
        problems = check_explainers(args.explainers)
        for problem in problems:
            print(problem, file=sys.stderr)
        print("explainers OK" if not problems else f"explainers DRIFT {len(problems)}")
        return 1 if problems else 0

    fetcher = None if args.offline else Fetcher()
    if args.corpus is not None:
        return run_corpus(args, fetcher)
    if args.release_src is None:
        args.release_src = Path("release-src")
    return run_legacy(args, fetcher)


if __name__ == "__main__":
    raise SystemExit(main())
