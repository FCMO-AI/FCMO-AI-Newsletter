#!/usr/bin/env python3
"""Render the FCMO AI Newsletter as a small, readable multilingual email.

The renderer is deliberately data-only: it accepts already published Story
records, escapes every reader-facing value, and emits both HTML and plain text.
Delivery is separate; this module never sends mail or translates content.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from typing import Any, Iterable
from urllib.parse import quote
from pathlib import Path
import json


MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)
SUBSCRIPTIONS = json.loads((Path(__file__).resolve().parents[1] / "community/config/subscriptions.json").read_text(encoding="utf-8"))
PAPER_NAME = SUBSCRIPTIONS["products"]["paper"]["name"]
LETTER_NAME = SUBSCRIPTIONS["products"]["letter"]["name"]
EMAIL_COPY = {
    "en": ("en", "Today's essentials", "Why it matters", "Read the analysis", "Preferences", "Unsubscribe", "Essential AI news", "5-minute read", "This edition preserves the distinctions between evidence, importance, and what we do not yet know."),
    "es-419": ("es-MX", "Lo esencial hoy", "Por qué importa", "Leer el análisis", "Preferencias", "Cancelar suscripción", "Lo esencial de inteligencia artificial", "lectura en 5 minutos", "Esta edición conserva las distinciones entre evidencia, importancia y lo que aún no sabemos."),
    "zh-Hans": ("zh-Hans", "今日要闻", "为什么重要", "阅读分析", "订阅偏好", "退订", "人工智能重要资讯", "5 分钟阅读", "本期保留证据、重要性与尚未解决的问题之间的区别。"),
}


def email_escape(value: Any, quote: bool = True) -> str:
    # Listmonk compiles Go templates. Editorial text must not become executable
    # template expressions even though braces are safe in ordinary HTML.
    return escape(str(value), quote=quote).replace("{{", "&#123;&#123;").replace("}}", "&#125;&#125;")


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    preheader: str
    html: str
    text: str


def render_letter_email(title: str, message: str, *, ghost_url: str, postal_address: str) -> RenderedEmail:
    """Preview-safe Spanish letter shell for Javier's Ghost editorial workflow.

    Ghost still owns the actual post editor, send action, and member footer.
    ``message`` is plain text so caller content cannot inject email markup.
    """
    if not title.strip() or not message.strip() or not ghost_url.strip() or not postal_address.strip():
        raise ValueError("letter title, message, Ghost URL and postal address are required")
    account = ghost_url.rstrip("/") + "/#/portal/account"
    paragraphs = [part.strip() for part in message.split("\n\n") if part.strip()]
    body = "".join(f'<p style="margin:0 0 18px;font:18px/1.6 Georgia,serif">{escape(part).replace(chr(10), "<br>")}</p>' for part in paragraphs)
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{escape(title)}</title></head>'
            f'<body style="margin:0;background:#f2efe8;color:#0a0a0a"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td align="center" style="padding:24px 12px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#fbf9f4">'
            f'<tr><td style="padding:28px;border-top:3px solid #f05a28"><p style="color:#a9340e;font:700 12px Arial,sans-serif;letter-spacing:.12em">fCMO · {escape(LETTER_NAME)}</p>'
            f'<h1 style="font:700 36px/1.1 Arial,sans-serif">{escape(title)}</h1>{body}<p style="font:16px Georgia,serif">— Javier</p></td></tr>'
            f'<tr><td style="padding:20px 28px;background:#f2efe8;color:#5e5a53;font:12px Arial,sans-serif">{escape(postal_address)}<br>'
            f'<a href="{escape(account, quote=True)}">Preferencias y baja</a></td></tr></table></td></tr></table></body></html>')
    text = f'{LETTER_NAME}\n{title}\n\n{message}\n\n— Javier\n\n{postal_address}\nPreferencias y baja: {account}\n'
    return RenderedEmail(subject=f'{LETTER_NAME}: {title}', preheader=paragraphs[0][:140], html=html, text=text)


def _edition_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value[:10])


def spanish_date(value: str | date) -> str:
    day = _edition_date(value)
    return f"{day.day} de {MONTHS[day.month - 1]} de {day.year}"


def _clean(value: Any, fallback: str = "") -> str:
    return str(value or fallback).strip()


def localized_story(story: dict[str, Any], locale: str = "es-419") -> dict[str, str] | None:
    """Return the complete native edition used by email, or ``None``.

    PENDING/FAILED records are intentionally not reconstructed from English.
    """
    if story.get("status") != "live":
        return None
    if locale == "en":
        fields = story
        title = _clean(fields.get("headline") or fields.get("title"))
        summary, why = _clean(fields.get("summary")), _clean(fields.get("why_it_matters"))
        return {"title": title, "summary": summary, "why_it_matters": why} if title and summary and why else None
    l10n = story.get("l10n", {}).get(locale)
    if not isinstance(l10n, dict) or l10n.get("state") not in {"NATIVE_ARB", "MACHINE_REVIEWED"}:
        return None
    if l10n.get("missing"):
        return None
    fields = l10n.get("fields")
    if not isinstance(fields, dict):
        return None
    title = _clean(fields.get("headline") or fields.get("title"))
    summary = _clean(fields.get("summary"))
    why = _clean(fields.get("why_it_matters"))
    if not title or not summary or not why:
        return None
    return {"title": title, "summary": summary, "why_it_matters": why}


def select_stories(stories: Iterable[dict[str, Any]] | dict[str, Any], minimum: int = 3, locale: str = "es-419") -> list[dict[str, Any]]:
    """Select the strongest complete Spanish stories in a deterministic order."""
    if isinstance(stories, dict):
        stories = stories.get("stories", [])
    ready = []
    for story in stories:
        fields = localized_story(story, locale)
        if fields is not None:
            ready.append({"story": story, "fields": fields})
    ready.sort(key=lambda item: (
        -int(item["story"].get("importance", 0)),
        str(item["story"].get("event_at", "")),
        str(item["story"].get("id", "")),
    ))
    return ready if len(ready) >= minimum else []


def story_url(story: dict[str, Any], site_url: str, locale: str = "es-419") -> str:
    explicit = story.get("url")
    if isinstance(explicit, str) and explicit.startswith(("https://", "http://")):
        return explicit
    slug = quote(_clean(story.get("slug") or story.get("id")), safe="-")
    prefix = {"en": "", "es-419": "es/", "zh-Hans": "zh/"}[locale]
    day = _clean(story.get("url_date") or story.get("event_at"))[:10].replace('-', '/')
    return f"{site_url.rstrip('/')}/{prefix}{day}/{slug}/"


def _subject(items: list[dict[str, Any]]) -> str:
    titles = [item["fields"]["title"] for item in items[:3]]
    subject = PAPER_NAME + ": " + " · ".join(titles)
    return subject if len(subject) <= 160 else subject[:157].rstrip() + "…"


def render_daily_email(
    stories: Iterable[dict[str, Any]],
    edition_date: str | date,
    *,
    site_url: str = "https://fcmo-ai.github.io/FCMO-AI-Newsletter",
    postal_address: str = "Domicilio editorial pendiente",
    preferences_url: str | None = None,
    unsubscribe_url: str | None = None,
    locale: str = "es-419",
) -> RenderedEmail:
    lang, heading, why_label, read_label, prefs_label, unsub_label, intro, minutes, evidence_note = EMAIL_COPY[locale]
    items = select_stories(stories, locale=locale)
    if not items:
        raise ValueError("at least three complete Spanish stories are required")
    rendered_date = spanish_date(edition_date) if locale == "es-419" else _edition_date(edition_date).isoformat()
    preheader = f"{intro} · {rendered_date}"
    preferences_url = preferences_url or f"{site_url.rstrip('/')}/#/portal/account"
    unsubscribe_url = unsubscribe_url or preferences_url
    cards_html: list[str] = []
    cards_text: list[str] = []
    for number, item in enumerate(items, 1):
        story = item["story"]
        fields = item["fields"]
        url = story_url(story, site_url, locale)
        title = email_escape(fields["title"])
        summary = email_escape(fields["summary"])
        why = email_escape(fields["why_it_matters"])
        link = email_escape(url, quote=True)
        cards_html.append(
            f"<article style=\"padding:0 0 24px;margin:0 0 24px;border-bottom:1px solid #c9c2b6\">"
            f"<p style=\"margin:0 0 8px;color:#a9340e;font:700 12px Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase\">{number:02d} · FCMO AI</p>"
            f"<h2 style=\"margin:0 0 10px;color:#0a0a0a;font:700 24px/1.1 Arial,sans-serif\"><a href=\"{link}\" style=\"color:#0a0a0a;text-decoration:none\">{title}</a></h2>"
            f"<p style=\"margin:0 0 10px;color:#34322f;font:16px/1.5 Georgia,serif\">{summary}</p>"
            f"<p style=\"margin:0;color:#34322f;font:15px/1.5 Arial,sans-serif\"><strong>{why_label}:</strong> {why}</p>"
            f"<p style=\"margin:12px 0 0;font:700 13px Arial,sans-serif\"><a href=\"{link}\" style=\"color:#a9340e\">{read_label} →</a></p>"
            "</article>"
        )
        cards_text.append(f"{number:02d}. {fields['title']}\n{fields['summary']}\n{why_label}: {fields['why_it_matters']}\n{read_label}: {url}")
    html = f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{email_escape(_subject(items))}</title></head>
<body style="margin:0;background:#f2efe8;color:#0a0a0a;font-family:Georgia,'Times New Roman',serif;overflow-wrap:anywhere">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0">{escape(preheader)}</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2efe8"><tr><td align="center" style="padding:28px 12px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#fbf9f4"><tr><td style="padding:28px 28px 12px;border-bottom:3px solid #0a0a0a">
      <p style="margin:0;color:#a9340e;font:700 12px Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase">{escape(PAPER_NAME)}</p>
      <h1 style="margin:10px 0 4px;color:#0a0a0a;font:700 36px/1 Arial,sans-serif;letter-spacing:-.04em">{heading}</h1>
      <p style="margin:0;color:#5e5a53;font:14px Arial,sans-serif">{escape(rendered_date)} · {minutes}</p>
    </td></tr><tr><td style="padding:28px">{''.join(cards_html)}
      <p style="margin:0;color:#5e5a53;font:14px/1.5 Arial,sans-serif">{evidence_note}</p>
    </td></tr><tr><td style="padding:20px 28px;background:#f2efe8;color:#5e5a53;font:12px/1.5 Arial,sans-serif">
      <p style="margin:0 0 8px"><strong>{escape(PAPER_NAME)}</strong></p><p style="margin:0 0 8px">{email_escape(postal_address)}</p>
      <p style="margin:0"><a href="{escape(preferences_url, quote=True)}" style="color:#a9340e">{prefs_label}</a> · <a href="{escape(unsubscribe_url, quote=True)}" style="color:#a9340e">{unsub_label}</a></p>
    </td></tr></table>
  </td></tr></table>
</body></html>'''
    text = PAPER_NAME + "\n" + heading + "\n" + rendered_date + "\n\n" + "\n\n".join(cards_text)
    text += f"\n\n{PAPER_NAME}\n{postal_address}\n{prefs_label}: {preferences_url}\n{unsub_label}: {unsubscribe_url}\n"
    return RenderedEmail(subject=_subject(items), preheader=preheader, html=html, text=text)
