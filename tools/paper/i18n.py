"""Source-controlled locale lookup and deterministic date formatting."""

from __future__ import annotations

from datetime import datetime
import json
from functools import lru_cache
from pathlib import Path
import unicodedata
from zoneinfo import ZoneInfo

COMPLETE_STATES = {"NATIVE_ARB", "MACHINE_REVIEWED"}
PROSE_FIELDS = ("title", "headline", "dek", "summary", "why_it_matters", "importance_rationale",
                "technical", "evidence", "related", "body", "sections", "captions")


def load_catalogs(root: Path) -> dict[str, dict]:
    result = {}
    for path in sorted((root / "i18n" / "ui").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        result[value["locale"]] = value
    return result


@lru_cache(maxsize=3)
def _catalog(locale_code: str) -> dict:
    path = Path(__file__).resolve().parents[2] / "i18n" / "ui" / f"{locale_code}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def story_locale(story: dict, locale_code: str, *, catalog: dict | None = None) -> dict:
    """Recount prose leaves instead of trusting a cached complete state."""
    try:
        from tools.validate_localizations import prose_leaves, path_text
    except ImportError:  # direct script execution from tools/
        from validate_localizations import prose_leaves, path_text

    if locale_code == "en":
        fields = {key: story.get(key) for key in PROSE_FIELDS}
        return {"state": "NATIVE_ARB", "fields": fields, "missing": []}
    entry = story.get("l10n", {}).get(locale_code) or {"state": "PENDING", "fields": {}, "missing": []}
    fields = entry.get("fields") or {}
    source = {key: story[key] for key in PROSE_FIELDS if key in story}
    # Derived display variants may use their translated semantic source. An
    # explicitly different headline or dek requires its own translated value.
    targets = dict(fields)
    if story.get("headline") == " ".join(str(story.get("title") or "").split()):
        targets.setdefault("headline", fields.get("title"))
    if story.get("dek") and " ".join(str(story.get("summary") or "").split()).startswith(story["dek"]):
        targets.setdefault("dek", fields.get("summary"))
    translated = dict(prose_leaves(targets))
    missing_paths = [path_text(path) for path, _ in prose_leaves(source) if path not in translated]
    media = story.get("media") or {}
    for key in ("caption", "alt"):
        value = media.get(key)
        # Generated explainer alt text is provided by the localized graphic;
        # free-form captions and alt strings need explicit locale prose.
        if isinstance(value, str) and value.strip() and not (fields.get("media") or {}).get(key):
            missing_paths.append(f"media.{key}")
        elif isinstance(value, dict) and value.get("en") and not value.get(locale_code) and key == "caption":
            missing_paths.append(f"media.{key}")
    for index, correction in enumerate(story.get("corrections") or []):
        for key in ("title", "text"):
            value = correction.get(key)
            if isinstance(value, dict) and value.get("en") and not value.get(locale_code):
                missing_paths.append(f"corrections[{index}].{key}")
            elif isinstance(value, str) and value.strip():
                localized = fields.get("corrections") or []
                if index >= len(localized) or not localized[index].get(key):
                    missing_paths.append(f"corrections[{index}].{key}")
    catalog = catalog if catalog is not None else _catalog(locale_code)
    groups = {"status": "story_status", "kind": "story_kind", "beat": "beat", "desk": "desk",
              "confidence": "confidence", "evidence_class": "evidence_class",
              "importance_tier": "importance_tier", "development_type": "development_type"}
    codes = [(group, story.get(key)) for key, group in groups.items()]
    evidence = story.get("evidence") or {}
    codes.extend(("claim_label", item.get("label")) for item in evidence.get("claims") or [])
    codes.extend(("gap_kind", item.get("kind")) for item in evidence.get("gaps") or [])
    codes.extend(("related_type", item.get("type")) for item in story.get("related") or [])
    codes.extend(("correction_kind", item.get("kind")) for item in story.get("corrections") or [])
    for group, code in codes:
        if code and not label(catalog, group, code):
            # Live corpus values can arrive before the frozen UI catalogue is
            # expanded.  Gap kinds have an explicit generic label, so an
            # otherwise complete native edition must not become translation
            # debt merely because its new enum value is not yet named.
            if group == "gap_kind" and label(catalog, group, "other"):
                continue
            missing_paths.append(f"labels.{group}.{code}")
    missing = list(dict.fromkeys([*(entry.get("missing") or []),
                                  *(".".join(path.split("[")[0].split(".")[:2]) if not path.startswith("labels.")
                                    else "labels" for path in missing_paths)]))
    state = entry.get("state", "PENDING")
    if missing and state in COMPLETE_STATES:
        state = "PENDING"
    # Rejected editions never expose their rejected fields in pending panels.
    return {**entry, "state": state, "fields": {} if state == "FAILED" else fields,
            "missing": missing, "missing_paths": missing_paths}


def is_complete(story: dict, locale_code: str, *, catalog: dict | None = None) -> bool:
    value = story_locale(story, locale_code, catalog=catalog)
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


def region_label(catalog: dict, code: object) -> str:
    """Reader label for a region code; a new corpus value falls back to the generic ``other`` label, never the raw code."""
    if code is None or code == "":
        return ""
    labels = catalog.get("labels", {}).get("region", {})
    return str(labels.get(str(code)) or labels.get("other", ""))


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
