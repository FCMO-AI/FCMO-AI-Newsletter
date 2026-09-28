"""Honest reader-visible newsroom status rendering."""

from __future__ import annotations

from html import escape

from .i18n import format_date, label, plural
from .routes import href


def freshness_sentence(freshness: dict, catalog: dict) -> str:
    """Plain-text corpus freshness sentence: the newest story's date and its lag."""
    strings = catalog["strings"]["freshness"]
    newest = freshness.get("newest_at")
    if newest is None:
        return strings["undated"]
    date = format_date(newest, catalog, precision="day")
    if freshness.get("lag_days") is None or freshness.get("checked_at") is None:
        return strings["newest"].format(newest=date)
    # Both ends are UTC calendar days, like every story date, so the newest story never reads as after the check.
    return strings["line"].format(newest=date, lag=plural(catalog, "freshness_day", freshness["lag_days"]),
                                  checked=format_date(freshness["checked_at"], catalog, precision="day"))


def freshness_attributes(freshness: dict) -> str:
    """``data-*`` attributes for a freshness element; unknown values are omitted."""
    attributes = f' data-freshness="{escape(str(freshness["state"]), quote=True)}"'
    for name, key in (("data-newest-at", "newest_at"), ("data-lag-hours", "lag_hours")):
        if freshness.get(key) is not None:
            attributes += f' {name}="{escape(str(freshness[key]), quote=True)}"'
    return attributes


def freshness_line(freshness: dict, catalog: dict) -> str:
    state = label(catalog, "freshness_state", freshness["state"])
    return (f'<p class="corpus-freshness"{freshness_attributes(freshness)}><strong>{escape(state)}</strong> '
            f'{escape(freshness_sentence(freshness, catalog))}</p>')


def render(status: dict, catalog: dict, *, base: str, locale: dict, freshness: dict | None = None) -> str:
    strings = catalog["strings"]["edition"]
    state = status["edition_state"]
    value = status.get("last_edition_at") or status.get("status_updated_at")
    date = format_date(value, catalog, precision="minute")
    status_url = href(base, locale["path_prefix"] + "status/")
    link = f' <a href="{escape(status_url, quote=True)}">{escape(strings["status_link"])}</a>'
    edition_at = escape(value, quote=True)
    corpus = freshness_line(freshness, catalog) if freshness is not None else ""
    if state == "FRESH":
        update = escape(strings["fresh"].format(date=date))
        stale = escape(strings["stale_page"].format(date=date)) + link
        return f'<p class="edition-update">{update}</p>{corpus}<div class="status-banner" hidden data-edition-state="FRESH" data-edition-at="{edition_at}"><!-- slot:banner -->{stale}</div>'
    if state == "QUIET":
        quiet_value = status.get("quiet_since") or value
        text = strings["quiet"].format(date=format_date(quiet_value, catalog, precision="minute"))
    elif state == "TRANSPORT_DOWN":
        text = strings["transport_down"].format(date=date) + link
    else:
        text = strings["delayed"].format(date=date) + link
    return f'<div class="status-banner" data-edition-state="{escape(state)}" data-edition-at="{edition_at}"><!-- slot:banner -->{text}</div>{corpus}'
