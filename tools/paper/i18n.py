"""Source-controlled locale lookup and deterministic date formatting."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import unicodedata
from zoneinfo import ZoneInfo

COMPLETE_STATES = {"NATIVE_ARB", "MACHINE_REVIEWED"}
PROSE_FIELDS = ("headline", "dek", "summary", "why_it_matters", "importance_rationale", "technical", "evidence")


def load_catalogs(root: Path) -> dict[str, dict]:
    result = {}
    for path in sorted((root / "i18n" / "ui").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        result[value["locale"]] = value
    return result


def story_locale(story: dict, locale_code: str) -> dict:
    if locale_code == "en":
        fields = {key: story.get(key) for key in PROSE_FIELDS}
        fields["title"] = story.get("title")
        return {"state": "NATIVE_ARB", "fields": fields, "missing": []}
    return story.get("l10n", {}).get(locale_code, {"state": "PENDING", "fields": {}, "missing": list(PROSE_FIELDS)})


def is_complete(story: dict, locale_code: str) -> bool:
    value = story_locale(story, locale_code)
    return value.get("state") in COMPLETE_STATES and not value.get("missing")


def field(story: dict, locale_code: str, key: str, default: object = "") -> object:
    if locale_code == "en":
        if key == "headline":
            return story.get("headline") or story.get("title", default)
        if key == "title":
            return story.get("title") or story.get("headline", default)
        return story.get(key, default)
    return story_locale(story, locale_code).get("fields", {}).get(key, default)


def headline(story: dict, locale_code: str, catalog: dict) -> str:
    value = field(story, locale_code, "headline") or field(story, locale_code, "title")
    if value:
        return str(value)
    return str(catalog["strings"]["l10n"]["pending_title"])


def dek(story: dict, locale_code: str, catalog: dict) -> str:
    value = field(story, locale_code, "dek") or field(story, locale_code, "summary")
    if value:
        return str(value)
    return catalog["strings"]["l10n"]["pending_notice"]


def label(catalog: dict, group: str, code: object, *, fallback: str = "") -> str:
    if code is None:
        return fallback
    labels = catalog.get("labels", {}).get(group, {})
    return str(labels.get(str(code), fallback))


def plural(catalog: dict, key: str, count: int) -> str:
    """Fill the catalog's plural form for ``count`` using the locale's plural rule."""
    forms = catalog["plurals"][key]
    category = "one" if catalog.get("plural_rule") == "one_other" and count == 1 else "other"
    return str(forms.get(category) or forms["other"]).format(count=count)


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_date(value: str, catalog: dict, *, precision: str = "day", include_time: bool = False) -> str:
    date_info = catalog["date"]
    dt = _parse(value)
    if precision in {"minute", "hour"}:
        dt = dt.astimezone(ZoneInfo(catalog.get("timezone", "America/Mexico_City")))
    pattern_key = "datetime" if include_time else "date_long"
    pattern = date_info["patterns"][pattern_key]
    hour12 = dt.hour % 12 or 12
    replacements = {
        "year": str(dt.year), "month": date_info["months"][dt.month - 1],
        "month_short": date_info["months_short"][dt.month - 1], "month_number": str(dt.month),
        "day": str(dt.day), "weekday": date_info["weekdays"][dt.weekday()],
        "hour12": str(hour12), "hour24": f"{dt.hour:02d}", "minute": f"{dt.minute:02d}",
        "ampm": date_info.get("am_pm", ["", ""])[dt.hour >= 12], "tz": date_info["tz_label"],
        "date": date_info["patterns"]["date_long"].format(
            year=dt.year, month=date_info["months"][dt.month - 1], month_number=dt.month,
            month_short=date_info["months_short"][dt.month - 1], day=dt.day,
            weekday=date_info["weekdays"][dt.weekday()]
        ),
    }
    return pattern.format(**replacements)


def _is_wide(char: str) -> bool:
    return unicodedata.east_asian_width(char) in {"W", "F"}


def visual_width(text: str) -> int:
    """Count wide and fullwidth (CJK) characters as two columns and every other character as one."""
    return sum(2 if _is_wide(char) else 1 for char in str(text))


def _is_word_char(char: str) -> bool:
    return char.isascii() and char.isalnum()


def truncate(text: str, limit: int = 160) -> str:
    """Shorten ``text`` so the result, ellipsis included, is at most ``limit`` columns wide.

    A kept prefix without wide characters is shortened exactly as before, at the last
    space. A prefix with wide characters is cut at a character boundary, backing out of
    a Latin word or number it would split, and loses trailing ASCII or CJK punctuation.
    """
    text = " ".join(str(text).split())
    if visual_width(text) <= limit:
        return text
    width = 0
    end = 0
    for char in text:
        width += 2 if _is_wide(char) else 1
        if width > limit - 1:
            break
        end += 1
    head = text[:end]
    if not any(_is_wide(char) for char in head):
        shortened = head.rsplit(" ", 1)[0]
        return (shortened or head).rstrip(".,;: ") + "…"
    if head and _is_word_char(head[-1]) and _is_word_char(text[end]):
        start = end
        while start > 0 and _is_word_char(text[start - 1]):
            start -= 1
        if start > 0:
            head = text[:start]
    return head.rstrip(".,;: ，、；：。") + "…"
