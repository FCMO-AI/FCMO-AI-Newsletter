"""Fail-open Ghost Content API adapter and localized community slots.

This module deliberately knows nothing about Ghost's Admin API or members. It
reads public posts once during a paper build and renders only an allowlisted
projection of those posts.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
import base64
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from .templates.subscribe import subscribe_block, ghost_signup_url, subscription_config


DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_RESPONSE_BYTES = 1_000_000
MAX_CARTAS = 3
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}
_SENSITIVE_QUERY_NAMES = {"email", "key", "token", "api_key", "access_token"}
_SUBSCRIBE_JS = Path(__file__).resolve().parents[2] / "site-src" / "assets" / "js" / "subscribe.js"


COPY = {
    "en": {
        "cartas_kicker": "FCMO · Human voices",
        "cartas_title": "Letters",
        "cartas_intro": "Weekly letters from Javier and Matías, written by people.",
        "subscribe_kicker": "FCMO AI · Stay with the signal",
        "inactive_title": "Subscriptions are coming soon",
        "active_title": "The Daily and Letters, in your inbox",
        "promise": "Read the daily FCMO AI paper, plus weekly human Letters from Javier and Matías that take ideas from Javier’s courses into practice.",
        "inactive": "Email signup is not active yet. Nothing will be submitted from this page.",
        "language": "The email edition will launch in Spanish; this edition remains available through feeds.",
        "rss": "Follow by RSS",
        "atom": "Follow by Atom",
        "notifications": "See all notification options",
        "portal": "Open Spanish email signup",
        "portal_title": "FCMO AI email signup",
        "portal_close": "Close",
        "portal_fallback": "Open signup in this page",
        "privacy": "No email address, membership record, or credential is stored in the newspaper.",
    },
    "es-419": {
        "cartas_kicker": "FCMO · Voces humanas",
        "cartas_title": "Cartas",
        "cartas_intro": "Cartas semanales de Javier y Matías, escritas por personas.",
        "subscribe_kicker": "FCMO AI · Sigue la señal",
        "inactive_title": "Las suscripciones llegarán pronto",
        "active_title": "El Diario y las Cartas, en tu correo",
        "promise": "Lee el diario FCMO AI y, cada semana, Cartas humanas de Javier y Matías que llevan a la práctica las ideas de los cursos de Javier.",
        "inactive": "El alta por correo todavía no está activa. Esta página no envía ningún dato.",
        "language": "La edición por correo se publicará en español.",
        "rss": "Seguir por RSS",
        "atom": "Seguir por Atom",
        "notifications": "Ver todas las opciones de notificación",
        "portal": "Abrir la suscripción por correo",
        "portal_title": "Suscripción por correo a FCMO AI",
        "portal_close": "Cerrar",
        "portal_fallback": "Abrir la suscripción en esta página",
        "privacy": "El periódico no guarda correos, membresías ni credenciales.",
    },
    "zh-Hans": {
        "cartas_kicker": "FCMO · 人类声音",
        "cartas_title": "来信",
        "cartas_intro": "Javier 与 Matías 每周亲自撰写的来信。",
        "subscribe_kicker": "FCMO AI · 持续关注信号",
        "inactive_title": "订阅即将开放",
        "active_title": "日报与来信，发送到你的邮箱",
        "promise": "阅读 FCMO AI 日报，以及 Javier 与 Matías 每周亲自撰写的来信，将 Javier 课程中的理念用于实践。",
        "inactive": "电子邮件订阅尚未开放；此页面不会提交任何数据。",
        "language": "电子邮件版将以西班牙语发布；你仍可通过订阅源阅读本语言版本。",
        "rss": "通过 RSS 关注",
        "atom": "通过 Atom 关注",
        "notifications": "查看所有通知选项",
        "portal": "打开西班牙语邮件订阅",
        "portal_title": "FCMO AI 电子邮件订阅",
        "portal_close": "关闭",
        "portal_fallback": "在此页面打开订阅",
        "privacy": "报纸不会存储电子邮箱、会员记录或凭据。",
    },
}


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _is_secure_or_local(parts: Any) -> bool:
    return parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in _LOOPBACK)


def _origin(parts: Any) -> tuple[str, str, int | None]:
    return parts.scheme, parts.hostname or "", parts.port


def _content_endpoint(content_url: str | None) -> tuple[str, Any] | None:
    if not isinstance(content_url, str) or not content_url.strip():
        return None
    try:
        parts = urlsplit(content_url.strip())
        if not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
            return None
        if not _is_secure_or_local(parts) or "/ghost/api/admin" in parts.path:
            return None
        path = parts.path.rstrip("/")
        if path.endswith("/ghost/api/content/posts"):
            endpoint_path = path + "/"
        elif path.endswith("/ghost/api/content"):
            endpoint_path = path + "/posts/"
        else:
            endpoint_path = path + "/ghost/api/content/posts/"
        endpoint = urlunsplit((parts.scheme, parts.netloc, endpoint_path, "", ""))
        return endpoint, urlsplit(endpoint)
    except (TypeError, ValueError):
        return None


def _safe_public_url(value: Any, content_origin: Any, *, image: bool = False) -> str | None:
    if value is None and image:
        return None
    if not isinstance(value, str) or not value:
        return None
    try:
        parts = urlsplit(value)
        if not parts.netloc or parts.username or parts.password or not _is_secure_or_local(parts):
            return None
        if _origin(parts) != _origin(content_origin):
            return None
        if image and not parts.path.startswith("/content/images/"):
            return None
        names = {name.casefold() for name, _ in parse_qsl(parts.query)}
        if names & _SENSITIVE_QUERY_NAMES:
            return None
        return value
    except (TypeError, ValueError):
        return None


def _published(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def fetch_cartas(content_url: str | None, api_key: str | None, *, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> list[dict[str, str | None]]:
    """Return at most three public ``cartas`` posts, or ``[]`` on any failure."""
    endpoint = _content_endpoint(content_url)
    if endpoint is None or not isinstance(api_key, str) or not api_key.strip():
        return []
    url, origin = endpoint
    query = urlencode({
        "key": api_key.strip(),
        "filter": "tag:cartas",
        "limit": str(MAX_CARTAS),
        "order": "published_at desc",
        "fields": "title,url,custom_excerpt,published_at,feature_image",
    })
    request = Request(url + "?" + query, headers={"Accept": "application/json", "User-Agent": "FCMO-AI-paper/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if not 200 <= response.getcode() < 300:
                return []
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            return []
        payload = json.loads(raw.decode("utf-8"))
        posts = payload.get("posts") if isinstance(payload, dict) else None
        if not isinstance(posts, list):
            return []
        projected: list[tuple[datetime, dict[str, str | None]]] = []
        for post in posts:
            if not isinstance(post, dict):
                return []
            title = post.get("title")
            excerpt = post.get("custom_excerpt")
            when = _published(post.get("published_at"))
            safe_url = _safe_public_url(post.get("url"), origin)
            if not isinstance(title, str) or not title.strip() or excerpt is not None and not isinstance(excerpt, str):
                return []
            if when is None or safe_url is None:
                return []
            item = {
                "title": title.strip(),
                "url": safe_url,
                "custom_excerpt": excerpt.strip() if isinstance(excerpt, str) else None,
                "published_at": post["published_at"],
                "feature_image": _safe_public_url(post.get("feature_image"), origin, image=True),
            }
            projected.append((when, item))
        projected.sort(key=lambda row: row[0], reverse=True)
        return [item for _, item in projected[:MAX_CARTAS]]
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return []


def _copy(locale_code: str) -> dict[str, str]:
    return COPY.get(locale_code, COPY["en"])


def _date(value: str, locale_code: str) -> str:
    parsed = _published(value)
    if parsed is None:
        return ""
    if locale_code == "es-419":
        months = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
        return f"{parsed.day} {months[parsed.month - 1]} {parsed.year}"
    if locale_code == "zh-Hans":
        return f"{parsed.year}年{parsed.month}月{parsed.day}日"
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    return f"{months[parsed.month - 1]} {parsed.day}, {parsed.year}"


def render_cartas(posts: list[dict[str, str | None]], locale_code: str) -> str:
    if not posts:
        return ""
    copy = _copy(locale_code)
    cards = []
    for post in posts[:MAX_CARTAS]:
        image = ""
        if post.get("feature_image"):
            image = f'<img src="{_e(post["feature_image"])}" alt="" loading="lazy">'
        excerpt = f'<p>{_e(post["custom_excerpt"])}</p>' if post.get("custom_excerpt") else ""
        cards.append(
            f'<article class="story-card">{image}<span class="card-meta">{_e(_date(str(post["published_at"]), locale_code))}</span>'
            f'<h3><a href="{_e(post["url"])}" rel="external noopener">{_e(post["title"])}</a></h3>{excerpt}</article>'
        )
    return (
        f'<section class="community-rail"><p class="section-kicker">{_e(copy["cartas_kicker"])}</p>'
        f'<h2>{_e(copy["cartas_title"])}</h2><p>{_e(copy["cartas_intro"])}</p>'
        f'<div class="card-row">{"".join(cards)}</div></section>'
    )


def without_empty_cartas_slot(page: str, cartas: str) -> str:
    """Remove A3's empty slot wrapper so an outage leaves no visual box."""
    if cartas:
        return page
    empty = '<div class="slot" data-slot="cartas"><!-- slot:cartas --></div>'
    return page.replace(empty, "", 1)


def portal_signup_url(portal_url: str | None) -> str | None:
    if not isinstance(portal_url, str) or not portal_url.strip():
        return None
    try:
        parts = urlsplit(portal_url.strip())
        if not parts.netloc or parts.username or parts.password or parts.query or not _is_secure_or_local(parts):
            return None
        fragment = parts.fragment or "/portal/signup"
        if fragment != "/portal/signup":
            return None
        return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/") + "/", "", fragment))
    except (TypeError, ValueError):
        return None


def subscribe_script_tag(base: str, locale_code: str, portal_url: str | None) -> str:
    if locale_code != "es-419" or portal_signup_url(portal_url) is None:
        return ""
    digest = base64.b64encode(hashlib.sha384(_SUBSCRIBE_JS.read_bytes()).digest()).decode("ascii")
    src = base.rstrip("/") + "/assets/js/subscribe.js"
    return f'<script defer src="{_e(src)}" integrity="sha384-{digest}" crossorigin="anonymous"></script>'


def _feed_links(base: str, path_prefix: str, copy: dict[str, str]) -> str:
    root = base.rstrip("/") + "/" + path_prefix.lstrip("/")
    return (
        '<ul class="community-options">'
        f'<li><a href="{_e(root + "feed.xml")}">{_e(copy["rss"])}</a></li>'
        f'<li><a href="{_e(root + "feed.atom")}">{_e(copy["atom"])}</a></li>'
        f'<li><a href="{_e(root + "feeds/")}">{_e(copy["notifications"])}</a></li>'
        "</ul>"
    )


def render_subscribe(*, locale_code: str, path_prefix: str, base: str, portal_url: str | None, page: bool = False) -> tuple[str, str]:
    # The old GHOST_PORTAL_URL remains an alias during the integration merge.
    import os
    ghost_url = os.environ.get("GHOST_URL") or portal_url
    if ghost_url and ghost_url.endswith("#/portal/signup"):
        ghost_url = ghost_url.split("#", 1)[0]
    html = subscribe_block("all" if page else "paper", locale_code, base=base,
                           path_prefix=path_prefix, ghost_url=ghost_url, page=page)
    css = f'<link rel="stylesheet" href="{_e(base.rstrip("/") + "/assets/subscribe/subscribe.css")}">'
    return html, css + subscribe_script_tag(base, locale_code, ghost_url)


def subscribe_page_title(locale_code: str, portal_url: str | None) -> str:
    import os
    if ghost_signup_url(os.environ.get('FCMO_EMAIL_PUBLIC_URL')):
        return {'en':'Get the FCMO AI Newsletter by email','es-419':'Recibe la Newsletter de FCMO AI por correo','zh-Hans':'通过邮件订阅 FCMO AI Newsletter'}[locale_code]
    config = subscription_config()
    ghost_url = os.environ.get("GHOST_URL") or portal_url
    if ghost_url and ghost_url.endswith("#/portal/signup"):
        ghost_url = ghost_url.split("#", 1)[0]
    copy = {"en": ("Choose the letters you want", "Subscriptions are coming soon"),
            "es-419": ("Elige lo que quieres recibir", "Las suscripciones llegarán pronto"),
            "zh-Hans": ("选择你想收到的内容", "订阅即将开放")}.get(locale_code, ("Choose the letters you want", "Subscriptions are coming soon"))
    return copy[0] if ghost_signup_url(ghost_url) and locale_code in config["languages"]["signup_locales"] else copy[1]
