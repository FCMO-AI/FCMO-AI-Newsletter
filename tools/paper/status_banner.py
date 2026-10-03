"""Honest reader-visible newsroom status rendering."""

from __future__ import annotations

from html import escape

from .i18n import format_date
from .routes import href


def render(status: dict, catalog: dict, *, base: str, locale: dict) -> str:
    strings = catalog["strings"]["edition"]
    state = status["edition_state"]
    value = status.get("last_edition_at") or status.get("status_updated_at")
    date = format_date(value, catalog, precision="minute")
    status_url = href(base, locale["path_prefix"] + "status/")
    link = f' <a href="{escape(status_url, quote=True)}">{escape(strings["status_link"])}</a>'
    edition_at = escape(value, quote=True)
    if state == "FRESH":
        update = escape(strings["fresh"].format(date=date))
        stale = escape(strings["stale_page"].format(date=date)) + link
        return f'<p class="edition-update">{update}</p><div class="status-banner" hidden data-edition-state="FRESH" data-edition-at="{edition_at}"><!-- slot:banner -->{stale}</div>'
    if state == "QUIET":
        quiet_value = status.get("quiet_since") or value
        text = strings["quiet"].format(date=format_date(quiet_value, catalog, precision="minute"))
    elif state == "TRANSPORT_DOWN":
        text = strings["transport_down"].format(date=date) + link
    else:
        text = strings["delayed"].format(date=date) + link
    return f'<div class="status-banner" data-edition-state="{escape(state)}" data-edition-at="{edition_at}"><!-- slot:banner -->{text}</div>'
