"""Subscription copy and stable block API for the static publication.

Ghost owns member data, confirmation, preferences, and unsubscribe. This
module emits no email form when Ghost is unconfigured or locale is not approved.
"""
from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

CONFIG = Path(__file__).resolve().parents[3] / "community/config/subscriptions.json"
_LOCALES = {
    "en": {"soon": "Subscriptions are coming soon", "ready": "Choose the letters you want", "intro": "Two publications, one membership. Choose either one or both.", "closed": "Email signup opens at launch. No information is sent from this page.", "language": "Email editions are in Spanish. Follow this edition through the feeds.", "cta": "Choose my emails", "manage": "Change preferences or leave at any time in your account.", "rss": "RSS", "json": "JSON feed"},
    "es-419": {"soon": "Las suscripciones llegarán pronto", "ready": "Elige lo que quieres recibir", "intro": "Dos publicaciones, una sola cuenta. Elige una o las dos.", "closed": "El alta por correo abre en el lanzamiento. Esta página no envía ningún dato.", "language": "Los correos se envían en español.", "cta": "Elegir mis correos", "manage": "Cambia tus preferencias o date de baja en cualquier momento desde tu cuenta.", "rss": "RSS", "json": "Feed JSON"},
    "zh-Hans": {"soon": "订阅即将开放", "ready": "选择你想收到的内容", "intro": "两份出版物，一个会员账户。可选择其中一份或两份。", "closed": "电子邮件订阅将在发布时开放。此页面不会提交任何数据。", "language": "电子邮件以西班牙语发送。你仍可通过订阅源阅读本语言版本。", "cta": "选择邮件", "manage": "你可以随时在账户中更改偏好或退订。", "rss": "RSS", "json": "JSON 订阅源"},
}
_DESCRIPTIONS = {
    "en": ("Javier’s plain-language letters, from FCMO Group.", "Matías’s technical paper digest, from FCMO AI."),
    "es-419": ("Cartas claras y cercanas de Javier, desde FCMO Group.", "El resumen técnico de Matías, desde FCMO AI."),
    "zh-Hans": ("Javier 的 FCMO Group 来信，清晰亲切。", "Matías 的 FCMO AI 技术摘要。"),
}


def subscription_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def ghost_signup_url(value: str | None) -> str | None:
    """Accept only a clean HTTPS or loopback origin; never reflect query secrets."""
    if not value:
        return None
    try:
        parts = urlsplit(value.strip())
        if not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
            return None
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1", "::1"}):
            return None
        if parts.path not in {"", "/"}:
            return None
        return urlunsplit((parts.scheme, parts.netloc, "/", "", "/portal/signup"))
    except ValueError:
        return None


def subscribe_block(zone: str, locale: str, *, base: str = "/FCMO-AI-Newsletter/", path_prefix: str | None = None,
                    ghost_url: str | None = None, page: bool = False) -> str:
    """Render the landing/page CTA. ``zone`` is ``letter``, ``paper``, or ``all``."""
    if zone not in {"letter", "paper", "all"}:
        raise ValueError("unknown subscription zone")
    config = subscription_config()
    copy = _LOCALES.get(locale, _LOCALES["en"])
    descriptions = _DESCRIPTIONS.get(locale, _DESCRIPTIONS["en"])
    configured_url = ghost_url if ghost_url is not None else os.environ.get("GHOST_URL") or os.environ.get("GHOST_PORTAL_URL")
    if configured_url and configured_url.endswith("#/portal/signup"):
        configured_url = configured_url.split("#", 1)[0]
    ghost = ghost_signup_url(configured_url)
    active = ghost is not None and locale in config["languages"]["signup_locales"]
    root = base.rstrip("/") + "/" + (path_prefix if path_prefix is not None else {"es-419": "es/", "zh-Hans": "zh/"}.get(locale, ""))
    items = []
    for key, description in zip(("letter", "paper"), descriptions):
        product = config["products"][key]
        items.append(f'<li class="subscribe-choice subscribe-choice--{key}"><strong>{escape(product["name"])}</strong><span>{escape(description)}</span></li>')
    action = (f'<p><a class="button" href="{escape(ghost, quote=True)}" rel="external noopener" data-ghost-portal="signup">{escape(copy["cta"])}</a></p>' if active else
              f'<p class="subscription-state"><strong>{escape(copy["closed"])}</strong></p>')
    title = copy["ready"] if active else copy["soon"]
    manage = copy["manage"] if active else {"en": "When signup opens, you can change or leave at any time.", "es-419": "Cuando abra el alta, podrás cambiar tus preferencias o darte de baja cuando quieras.", "zh-Hans": "开放订阅后，你可以随时更改偏好或退订。"}.get(locale, copy["manage"])
    tag = "h1" if page else "h2"
    wrapper = "subscribe-page" if page else "subscribe-card"
    heading = f'<{tag} class="page-title">{escape(title)}</{tag}>'
    return (f'<section class="{wrapper} subscribe-v2" data-subscribe-zone="{zone}" data-subscribe-state="{"active" if active else "launch"}">'
            f'<p class="section-kicker">FCMO Group × FCMO AI</p>{heading}<p>{escape(copy["intro"])}</p>'
            f'<ul class="subscribe-choices">{"".join(items)}</ul>{action}<p>{escape(manage)}</p>'
            f'<p>{escape(copy["language"])}</p><ul class="community-options">'
            f'<li><a href="{escape(root + "feed.xml", quote=True)}">{escape(copy["rss"])}</a></li>'
            f'<li><a href="{escape(root + "feed.atom", quote=True)}">Atom</a></li>'
            f'<li><a href="{escape(root + "feed.json", quote=True)}">{escape(copy["json"])}</a></li></ul></section>')
