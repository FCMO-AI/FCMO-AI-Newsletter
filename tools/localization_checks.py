"""Provider-free Spanish and Chinese fidelity checks the strict gate adds on top of
numbers/IDs/URLs: scale words (million/billion), English importance-tier terms, and
English sentences hidden inside an otherwise translated field.

These are deterministic invariants, not a translation judge. They exist because the
whole-field `looks_english` heuristic and the digit-token check both pass a field that
says "2.7-3.7 millones de tokens" for "2.7-3.7 billion tokens" (the digits survive, the
magnitude is wrong), that drops "billion" entirely, or that leaves "Very major" in the
middle of a Spanish sentence.
"""
from __future__ import annotations

from collections import Counter
import re
from typing import Any, Iterable

# English scale words after a number: "13 million", "$60 billion", "2.7–3.7 billion",
# "US$2.6 million". The captured number is the one immediately before the scale word.
SCALE_EN = re.compile(
    r"(?<![A-Za-z])(\d+(?:[.,]\d+)*)\s*(?:[-–—]\s*\d+(?:[.,]\d+)*\s*)?(trillion|billion|million)s?(?![A-Za-z])", re.I)
SCALE_EN_RANGE = re.compile(
    r"(?<![A-Za-z])(\d+(?:[.,]\d+)*)\s*[-–—]\s*(\d+(?:[.,]\d+)*)\s*(trillion|billion|million)s?(?![A-Za-z])", re.I)

# Accepted renderings that keep the source digits unchanged (the gate requires that).
# es-419 uses the long scale: billion = "mil millones", trillion = "billones".
SCALE_TARGET: dict[str, dict[str, re.Pattern[str]]] = {
    "es-419": {
        "million": re.compile(r"\s*(?:de\s+)?(?:millones|millón)(?![a-záéíóúñ])", re.I),
        "billion": re.compile(r"\s*(?:de\s+)?mil\s+millones(?![a-záéíóúñ])", re.I),
        "trillion": re.compile(r"\s*(?:de\s+)?(?:billones|billón)(?![a-záéíóúñ])", re.I),
    },
    "zh-Hans": {
        "million": re.compile(r"\s*百万"),
        "billion": re.compile(r"\s*十亿"),
        "trillion": re.compile(r"\s*万亿"),
    },
}
NUMBER = r"\d+(?:[.,]\d+)*"
_RANGE_END = re.compile(rf"\s*[-–—]\s*{NUMBER}")
_LATIN_SCALE = re.compile(r"\s*(trillion|billion|million)s?(?![A-Za-z])", re.I)


def scale_mentions(text: str) -> Counter[tuple[str, str]]:
    """Multiset of (number, scale) in English text; a range counts both ends."""
    found: Counter[tuple[str, str]] = Counter()
    consumed: list[tuple[int, int]] = []
    for m in SCALE_EN_RANGE.finditer(text):
        scale = m.group(3).lower()
        found[(m.group(1), scale)] += 1
        found[(m.group(2), scale)] += 1
        consumed.append(m.span())
    for m in SCALE_EN.finditer(text):
        if any(a <= m.start() < b for a, b in consumed):
            continue
        found[(m.group(1), m.group(2).lower())] += 1
    return found


def _classify_tail(tail: str, locale: str) -> str | None:
    """Which scale (million/billion/trillion) the text right after a number states."""
    range_end = _RANGE_END.match(tail)
    if range_end:
        tail = tail[range_end.end():]
    for scale, pattern in SCALE_TARGET[locale].items():
        if pattern.match(tail):
            return scale
    latin = _LATIN_SCALE.match(tail)
    if latin:
        return latin.group(1).lower()
    abbreviation = re.match(r"([MBT])(?![A-Za-z])", tail)
    if abbreviation:  # "600B", "29–121M": the unit letter carries the scale
        return {"M": "million", "B": "billion", "T": "trillion"}[abbreviation.group(1)]
    if locale == "es-419" and re.match(r"\s*(?:de\s+)?(?:millones|millón|mil\s+millones|billones|billón)", tail, re.I):
        return "other"
    if locale == "zh-Hans" and re.match(r"\s*(?:万|亿)", tail):
        return "other"
    return None


def magnitude_errors(source_text: str, target_text: str, locale: str) -> list[str]:
    """Every English "<number> <million|billion|trillion>" must survive with the same
    digits and the matching scale. A wrong scale ("billion" written "millones") and a
    dropped scale (zh "处理2.7个token") are errors. An English scale word left as is
    ("13 million" inside Chinese) keeps its magnitude and is reported separately by
    ``untranslated_scales``."""
    if locale not in SCALE_TARGET:
        return []
    problems: list[str] = []
    for (number, scale), want in sorted(scale_mentions(source_text).items()):
        seen: Counter[str | None] = Counter()
        for m in re.finditer(rf"(?<![\d.,]){re.escape(number)}(?!\d|[.,]\d)", target_text):
            seen[_classify_tail(target_text[m.end():m.end() + 40], locale)] += 1
        if seen[scale] >= want:
            continue
        if seen["other"] or any(k not in (None, scale, "other") for k in seen):
            problems.append(f"magnitude changed: {number} {scale} is written with a different scale word")
        else:
            problems.append(f"magnitude lost: {number} {scale} has no scale word in the {locale} text")
    return problems


def untranslated_scales(text: str, locale: str) -> list[str]:
    """English scale words left in a Spanish or Chinese field (legible, but untranslated)."""
    return [m.group(0).strip() for m in SCALE_EN.finditer(text)] if locale in SCALE_TARGET else []


# Importance-tier terms of the UI catalogue (labels.importance_tier keys) that have no
# meaning in Spanish or Chinese prose. "Notable" is a real Spanish word and is exempt.
TIER_TERMS = ("Very major", "Major", "Minor", "Field-shifting", "Paradigm-level",
              "Meaningful", "Alien evidence")
TIER_RE = re.compile(r"(?<![^\W\d_])(?:" + "|".join(re.escape(t) for t in TIER_TERMS) + r")(?![^\W\d_]|-)", re.I)


def english_tier_terms(text: str) -> list[str]:
    return [m.group(0) for m in TIER_RE.finditer(text)]


_SENT = re.compile(r"(?<=[.!?;。！？；])\s+")
EN_STOP = frozenset(
    "the and of to is that with for this are was which from by on not it be have its "
    "than an or as at were but their these those into if would could should will may "
    "can has had been being they them there here when where while what who whom whose "
    "also only over under between within without".split())
_LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
_ANY_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
_LATIN_RUN = re.compile(r"(?:[A-Za-z][A-Za-z'’-]*[\s,;:()\"“”]+){3,}[A-Za-z][A-Za-z'’-]*")


def english_sentences(text: str, locale: str) -> list[str]:
    """Sentences that are English prose inside a field the author called translated."""
    found: list[str] = []
    if locale == "zh-Hans":
        for run in _LATIN_RUN.finditer(text):
            words = [w.lower() for w in _LATIN_WORD.findall(run.group(0))]
            if len(words) >= 4 and sum(w in EN_STOP for w in words) >= 2:
                found.append(run.group(0))
        return found
    for sentence in _SENT.split(text):
        words = [w.lower() for w in _ANY_WORD.findall(sentence)]
        stop = sum(w in EN_STOP for w in words)
        if len(words) >= 6 and stop >= 3 and stop / len(words) >= 0.25:
            found.append(sentence)
    return found
