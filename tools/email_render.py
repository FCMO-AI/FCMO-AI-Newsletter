#!/usr/bin/env python3
"""Render the FCMO AI Diario as a small, readable, Spanish email.

The renderer is deliberately data-only: it accepts already published Story
records, escapes every reader-facing value, and emits both HTML and plain text.
Ghost remains the delivery system; this module never sends mail.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from typing import Any, Iterable
from urllib.parse import quote


MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    preheader: str
    html: str
    text: str


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
    l10n = story.get("l10n", {}).get(locale)
    if not isinstance(l10n, dict) or l10n.get("state") not in {"NATIVE_ARB", "MACHINE_REVIEWED"}:
        return None
    if l10n.get("missing"):
        return None
    fields = l10n.get("fields")
    if not isinstance(fields, dict):
        return None
    title = _clean(fields.get("headline") or fields.get("title") or story.get("headline") or story.get("title"))
    summary = _clean(fields.get("summary") or story.get("summary"))
    why = _clean(fields.get("why_it_matters") or story.get("why_it_matters"))
    if not title or not summary or not why:
        return None
    return {"title": title, "summary": summary, "why_it_matters": why}


def select_stories(stories: Iterable[dict[str, Any]] | dict[str, Any], minimum: int = 3) -> list[dict[str, Any]]:
    """Select the strongest complete Spanish stories in a deterministic order."""
    if isinstance(stories, dict):
        stories = stories.get("stories", [])
    ready = []
    for story in stories:
        fields = localized_story(story)
        if fields is not None:
            ready.append({"story": story, "fields": fields})
    ready.sort(key=lambda item: (
        -int(item["story"].get("importance", 0)),
        str(item["story"].get("event_at", "")),
        str(item["story"].get("id", "")),
    ))
    return ready if len(ready) >= minimum else []


def story_url(story: dict[str, Any], site_url: str) -> str:
    explicit = story.get("url")
    if isinstance(explicit, str) and explicit.startswith(("https://", "http://")):
        return explicit
    slug = quote(_clean(story.get("slug") or story.get("id")), safe="-")
    return f"{site_url.rstrip('/')}/es/{slug}/"


def _subject(items: list[dict[str, Any]]) -> str:
    titles = [item["fields"]["title"] for item in items[:3]]
    subject = "FCMO AI Diario: " + " · ".join(titles)
    return subject if len(subject) <= 160 else subject[:157].rstrip() + "…"


def render_daily_email(
    stories: Iterable[dict[str, Any]],
    edition_date: str | date,
    *,
    site_url: str = "https://fcmo-ai.github.io/FCMO-AI-Newsletter",
    postal_address: str = "Domicilio editorial pendiente",
    preferences_url: str | None = None,
    unsubscribe_url: str | None = None,
) -> RenderedEmail:
    items = select_stories(stories)
    if not items:
        raise ValueError("at least three complete Spanish stories are required")
    rendered_date = spanish_date(edition_date)
    preheader = f"Lo esencial de inteligencia artificial · {rendered_date}"
    preferences_url = preferences_url or f"{site_url.rstrip('/')}/portal/"
    unsubscribe_url = unsubscribe_url or preferences_url
    cards_html: list[str] = []
    cards_text: list[str] = []
    for number, item in enumerate(items, 1):
        story = item["story"]
        fields = item["fields"]
        url = story_url(story, site_url)
        title = escape(fields["title"])
        summary = escape(fields["summary"])
        why = escape(fields["why_it_matters"])
        link = escape(url, quote=True)
        cards_html.append(
            f"<article style=\"padding:0 0 24px;margin:0 0 24px;border-bottom:1px solid #d8d4ca\">"
            f"<p style=\"margin:0 0 8px;color:#8a3224;font:700 12px Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase\">{number:02d} · FCMO AI</p>"
            f"<h2 style=\"margin:0 0 10px;color:#171717;font:700 24px/1.1 Georgia,serif\"><a href=\"{link}\" style=\"color:#171717;text-decoration:none\">{title}</a></h2>"
            f"<p style=\"margin:0 0 10px;color:#44413b;font:16px/1.5 Georgia,serif\">{summary}</p>"
            f"<p style=\"margin:0;color:#44413b;font:15px/1.5 Arial,sans-serif\"><strong>Por qué importa:</strong> {why}</p>"
            f"<p style=\"margin:12px 0 0;font:700 13px Arial,sans-serif\"><a href=\"{link}\" style=\"color:#7c291e\">Leer el análisis →</a></p>"
            "</article>"
        )
        cards_text.append(f"{number:02d}. {fields['title']}\n{fields['summary']}\nPor qué importa: {fields['why_it_matters']}\nLeer: {url}")
    html = f'''<!doctype html>
<html lang="es-MX"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{escape(_subject(items))}</title></head>
<body style="margin:0;background:#f4f1e9;color:#171717;font-family:Georgia,'Times New Roman',serif">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0">{escape(preheader)}</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1e9"><tr><td align="center" style="padding:28px 12px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px;background:#fffdf8"><tr><td style="padding:28px 28px 12px;border-bottom:3px solid #171717">
      <p style="margin:0;color:#b84b2f;font:700 12px Arial,sans-serif;letter-spacing:.14em;text-transform:uppercase">FCMO AI · Diario</p>
      <h1 style="margin:10px 0 4px;color:#171717;font:700 36px/1 Georgia,serif;letter-spacing:-.04em">Lo esencial hoy</h1>
      <p style="margin:0;color:#5f5d58;font:14px Arial,sans-serif">{escape(rendered_date)} · lectura en 5 minutos</p>
    </td></tr><tr><td style="padding:28px">{''.join(cards_html)}
      <p style="margin:0;color:#5f5d58;font:14px/1.5 Arial,sans-serif">Esta edición conserva las distinciones entre evidencia, importancia y lo que aún no sabemos.</p>
    </td></tr><tr><td style="padding:20px 28px;background:#e9e5da;color:#5f5d58;font:12px/1.5 Arial,sans-serif">
      <p style="margin:0 0 8px"><strong>FCMO AI Newsletter</strong></p><p style="margin:0 0 8px">{escape(postal_address)}</p>
      <p style="margin:0"><a href="{escape(preferences_url, quote=True)}" style="color:#7c291e">Preferencias</a> · <a href="{escape(unsubscribe_url, quote=True)}" style="color:#7c291e">Cancelar suscripción</a></p>
    </td></tr></table>
  </td></tr></table>
</body></html>'''
    text = "FCMO AI · Diario\nLo esencial hoy\n" + rendered_date + "\n\n" + "\n\n".join(cards_text)
    text += f"\n\nFCMO AI Newsletter\n{postal_address}\nPreferencias: {preferences_url}\nCancelar suscripción: {unsubscribe_url}\n"
    return RenderedEmail(subject=_subject(items), preheader=preheader, html=html, text=text)
