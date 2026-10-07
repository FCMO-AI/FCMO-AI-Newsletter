#!/usr/bin/env python3
"""Normalize upstream development records to record.v3 (contracts/record.v3.schema.json).

Today's upstream rows (record.v2) drift: 15+ desk spellings, free-text confidence,
21 claim labels, country names instead of ISO codes, language names instead of
BCP 47 tags. This module maps that drift onto the closed vocabularies of the
contract and validates each record on its own. A row that cannot be normalized is
quarantined with a public reason code instead of failing the whole batch.

Standard library only. Tools never import from tests/.

    python3 tools/taxonomy.py check corpus            # one line per quarantined row
    python3 tools/taxonomy.py normalize corpus --out records.v3.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

RECORD_SCHEMA = "fcmo-record-v3"
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
UTC_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

BEATS = ("technology", "business", "policy", "society", "research")
DESKS = (
    "architectures_scaling", "reasoning_posttraining", "agents_memory",
    "multimodality_world_models", "evaluation_science", "compute_inference",
    "labs_industry", "policy_geopolitics",
)
CONFIDENCE = ("confirmed", "strongly_supported", "supported", "supported_with_limits", "claimed_unverified")
CLAIM_LABELS = ("DEMONSTRATED", "CLAIMED", "INFERRED", "SPECULATIVE", "DISPUTED", "NOT_ESTABLISHED")
DEVELOPMENT_TYPES = (
    "paper", "technical_report", "model_release", "product_release", "repository_release",
    "dataset_benchmark", "hardware_infrastructure", "industry_transaction", "policy_action",
    "organizational",
)
TIERS = ("Notable", "Meaningful", "Major", "Very major", "Field-shifting", "Paradigm-level")
RECORD_STATUS = ("active", "developing", "withdrawn", "superseded")
WITHDRAWAL_REASONS = ("UPSTREAM_RETRACTION", "DUPLICATE", "FACTUAL_ERROR", "RIGHTS", "PRIVACY", "LEGAL", "EDITORIAL")
RELATION_TYPES = ("related", "follow_up", "duplicate_of", "supersedes")
DATE_PRECISIONS = ("minute", "hour", "day", "month")

# English prose keys of a record, in the order the locale overlay uses them.
PROSE_KEYS = (
    "title", "summary", "why_it_matters", "why", "importance_rationale", "limitations",
    "contradictory_evidence", "claims", "evidence_gaps", "relationships", "technical",
)

# ---------------------------------------------------------------------------------------
# Vocabulary maps. Keys are compared after _key(): lower case, any run of
# non-alphanumerics collapsed to "_". Explicit entries first; token rules second.
# ---------------------------------------------------------------------------------------
DESK_MAP = {
    "architectures_scaling": "architectures_scaling",
    "architectures": "architectures_scaling",
    "scaling": "architectures_scaling",
    "training_data": "architectures_scaling",
    "pretraining": "architectures_scaling",
    "reasoning_posttraining": "reasoning_posttraining",
    "reasoning_posttraining_rl": "reasoning_posttraining",
    "reasoning": "reasoning_posttraining",
    "posttraining": "reasoning_posttraining",
    "agents_memory": "agents_memory",
    "agents": "agents_memory",
    "multimodality": "multimodality_world_models",
    "multimodality_world_models": "multimodality_world_models",
    "multimodality_world_models_robotics": "multimodality_world_models",
    "world_models": "multimodality_world_models",
    "robotics": "multimodality_world_models",
    "evaluation_science": "evaluation_science",
    "evaluation_science_interpretability": "evaluation_science",
    "interpretability": "evaluation_science",
    "compute_inference": "compute_inference",
    "compute_hardware": "compute_inference",
    "inference_systems": "compute_inference",
    "efficiency": "compute_inference",
    "efficiency_compression": "compute_inference",
    "efficiency_quantization_sparsity_compression": "compute_inference",
    "labs_industry": "labs_industry",
    "open_models": "labs_industry",
    "open_ecosystem": "labs_industry",
    "open_models_ecosystem": "labs_industry",
    "policy_geopolitics": "policy_geopolitics",
    "policy": "policy_geopolitics",
}
# Token fallback for unseen desk spellings: the first rule whose token is present wins.
DESK_TOKENS = (
    ("policy", "policy_geopolitics"), ("geopolitic", "policy_geopolitics"), ("regulat", "policy_geopolitics"),
    ("agent", "agents_memory"), ("memory", "agents_memory"),
    ("multimodal", "multimodality_world_models"), ("world_model", "multimodality_world_models"),
    ("robot", "multimodality_world_models"), ("vision", "multimodality_world_models"),
    ("eval", "evaluation_science"), ("interpret", "evaluation_science"), ("safety", "evaluation_science"),
    ("reason", "reasoning_posttraining"), ("posttrain", "reasoning_posttraining"), ("rl", "reasoning_posttraining"),
    ("compute", "compute_inference"), ("inference", "compute_inference"), ("hardware", "compute_inference"),
    ("efficien", "compute_inference"), ("chip", "compute_inference"),
    ("lab", "labs_industry"), ("industry", "labs_industry"), ("open", "labs_industry"), ("ecosystem", "labs_industry"),
    ("architect", "architectures_scaling"), ("scal", "architectures_scaling"), ("train", "architectures_scaling"),
)

DEVELOPMENT_TYPE_MAP = {
    "paper": "paper",
    "paper_case_study": "paper",
    "evaluation_science_interpretability": "paper",
    "technical_report": "technical_report",
    "model_release": "model_release",
    "model_or_system_release": "model_release",
    "model_release_and_technical_report": "model_release",
    "system_release": "model_release",
    "product_release": "product_release",
    "repository_release": "repository_release",
    "code_release": "repository_release",
    "dataset_benchmark": "dataset_benchmark",
    "dataset_or_benchmark": "dataset_benchmark",
    "benchmark": "dataset_benchmark",
    "dataset": "dataset_benchmark",
    "hardware_infrastructure": "hardware_infrastructure",
    "hardware_or_infrastructure": "hardware_infrastructure",
    "compute_hardware": "hardware_infrastructure",
    "industry_compute_infrastructure": "hardware_infrastructure",
    "infrastructure": "hardware_infrastructure",
    "industry_transaction": "industry_transaction",
    "industry_compute": "industry_transaction",
    "funding": "industry_transaction",
    "acquisition": "industry_transaction",
    "policy_action": "policy_action",
    "policy_security": "policy_action",
    "regulation": "policy_action",
    "legislation": "policy_action",
    "organizational": "organizational",
}
DEVELOPMENT_TYPE_TOKENS = (
    ("policy", "policy_action"), ("regulat", "policy_action"), ("legislat", "policy_action"),
    ("court", "policy_action"), ("law", "policy_action"),
    ("transaction", "industry_transaction"), ("funding", "industry_transaction"),
    ("acqui", "industry_transaction"), ("deal", "industry_transaction"), ("invest", "industry_transaction"),
    ("hardware", "hardware_infrastructure"), ("infrastructure", "hardware_infrastructure"),
    ("chip", "hardware_infrastructure"), ("datacenter", "hardware_infrastructure"),
    ("benchmark", "dataset_benchmark"), ("dataset", "dataset_benchmark"),
    ("repository", "repository_release"), ("code", "repository_release"),
    ("model", "model_release"), ("product", "product_release"), ("release", "model_release"),
    ("paper", "paper"), ("preprint", "paper"), ("study", "paper"),
    ("report", "technical_report"), ("organi", "organizational"), ("hire", "organizational"),
)

CONFIDENCE_MAP = {
    "confirmed": "confirmed",
    "strongly_supported": "strongly_supported",
    "supported": "supported",
    "supported_with_limits": "supported_with_limits",
    "claimed_unverified": "claimed_unverified",
    # Canonical ARB confidence: credible evidence is still unconfirmed. Keep it
    # in the unverified lane rather than quarantining it or promoting certainty.
    "credible_unconfirmed": "claimed_unverified",
    "strong_primary_formal_artifact_pending_independent_mathematical_review": "supported_with_limits",
    "supported_government_attribution_with_open_causal_gaps": "supported_with_limits",
    "primary_roadmap_commitment_not_delivered": "claimed_unverified",
    "vendor_specced_unbenchmarked": "claimed_unverified",
    "weak_signal": "claimed_unverified",
    "speculation": "claimed_unverified",
}

REGION_NAMES = {
    "global": "GLOBAL", "worldwide": "GLOBAL", "international": "GLOBAL",
    "eu": "EU", "european_union": "EU", "europe": "EU",
    "united_states": "US", "united_states_of_america": "US", "usa": "US", "us": "US", "u_s": "US",
    "china": "CN", "prc": "CN", "people_s_republic_of_china": "CN",
    "united_kingdom": "GB", "uk": "GB", "u_k": "GB", "great_britain": "GB", "britain": "GB", "england": "GB",
    "united_arab_emirates": "AE", "uae": "AE",
    "saudi_arabia": "SA", "qatar": "QA", "israel": "IL", "turkey": "TR", "egypt": "EG",
    "singapore": "SG", "netherlands": "NL", "taiwan": "TW", "south_korea": "KR", "korea": "KR",
    "republic_of_korea": "KR", "japan": "JP", "india": "IN", "malaysia": "MY", "indonesia": "ID",
    "vietnam": "VN", "thailand": "TH", "philippines": "PH", "australia": "AU", "new_zealand": "NZ",
    "canada": "CA", "mexico": "MX", "brazil": "BR", "argentina": "AR", "chile": "CL", "colombia": "CO",
    "france": "FR", "germany": "DE", "italy": "IT", "spain": "ES", "portugal": "PT", "ireland": "IE",
    "switzerland": "CH", "sweden": "SE", "norway": "NO", "denmark": "DK", "finland": "FI",
    "poland": "PL", "belgium": "BE", "austria": "AT", "russia": "RU", "ukraine": "UA",
    "south_africa": "ZA", "nigeria": "NG", "kenya": "KE", "hong_kong": "HK",
}
# A US state is reported as its country.
US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware",
    "florida", "georgia_us", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
    "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new_hampshire", "new_jersey", "new_mexico",
    "new_york", "north_carolina", "north_dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode_island", "south_carolina", "south_dakota", "tennessee", "texas", "utah", "vermont",
    "virginia", "washington", "west_virginia", "wisconsin", "wyoming", "district_of_columbia",
}
LANGUAGE_NAMES = {
    "english": "en", "spanish": "es", "chinese": "zh", "mandarin": "zh", "polish": "pl",
    "korean": "ko", "arabic": "ar", "japanese": "ja", "french": "fr", "german": "de",
    "portuguese": "pt", "italian": "it", "russian": "ru", "hindi": "hi", "dutch": "nl",
    "turkish": "tr", "hebrew": "he", "vietnamese": "vi", "indonesian": "id", "ukrainian": "uk",
}
BCP47 = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")

# Topic keywords that put a story on the society beat (safety, security, incidents,
# labour, rights). Matched as whole hyphen-separated tokens or exact slugs.
SOCIETY_TOPIC_TOKENS = {
    "cybersecurity", "cyber", "incident", "incidents", "incident-response", "misuse", "sandbox-escape",
    "sandboxing", "agent-safety", "jailbreak", "jailbreaks", "labor", "labour", "jobs", "employment",
    "workforce", "education", "election", "elections", "misinformation", "disinformation", "deepfake",
    "deepfakes", "copyright", "privacy", "surveillance", "child-safety", "mental-health", "bioweapons",
    "biosecurity", "fraud", "scams", "discrimination", "bias",
}

# Secondary outlets: a source on these domains is reporting, not the primary record.
SECONDARY_DOMAINS = {
    "reuters.com", "axios.com", "bloomberg.com", "techcrunch.com", "theverge.com", "tomshardware.com",
    "cnbc.com", "ft.com", "wsj.com", "nytimes.com", "theinformation.com", "venturebeat.com",
    "wired.com", "arstechnica.com", "apnews.com", "bbc.com", "bbc.co.uk", "theguardian.com",
    "scmp.com", "nikkei.com", "asia.nikkei.com", "businessinsider.com", "fortune.com", "forbes.com",
    "zdnet.com", "engadget.com", "siliconangle.com", "datacenterdynamics.com", "theregister.com",
    "anandtech.com", "servethehome.com", "hpcwire.com", "eetimes.com", "digitimes.com",
    "semafor.com", "politico.com", "politico.eu", "washingtonpost.com", "economist.com",
    "cnn.com", "news.ycombinator.com", "twitter.com", "x.com", "medium.com", "substack.com",
}

ABBREVIATIONS = {
    "e.g.", "i.e.", "vs.", "approx.", "inc.", "corp.", "ltd.", "co.", "no.", "fig.", "dr.", "mr.",
    "ms.", "mrs.", "st.", "jr.", "sr.", "al.", "etc.", "cf.", "est.", "u.s.", "u.k.", "u.n.",
    "e.u.", "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.", "oct.",
    "nov.", "dec.",
}

HEADLINE_MAX = 90
HEADLINE_MIN = 8
DEK_MAX = 240
DEK_MIN = 20


class Quarantine(ValueError):
    """A record that cannot be published; ``codes`` are public reason codes."""

    def __init__(self, codes: Iterable[str]):
        self.codes = sorted(set(codes))
        super().__init__(",".join(self.codes))


# ---------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------
def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def slugify(value: Any, max_len: int = 80) -> str:
    """ASCII slug: apostrophes vanish, any other run of non-alphanumerics becomes '-'.

    The result is cut at a hyphen so that it is at most ``max_len`` characters; it is
    a URL token, never reader-facing text.
    """
    folded = []
    for ch in unicodedata.normalize("NFKD", str(value or "")):
        if unicodedata.combining(ch) or ch in "'’`":
            continue  # accents fold into their letter; apostrophes vanish
        folded.append(ch.lower() if ch.isascii() and ch.isalnum() else "-")
    words = [w for w in "".join(folded).split("-") if w]
    out = ""
    for word in words:
        candidate = f"{out}-{word}" if out else word
        if len(candidate) > max_len:
            break
        out = candidate
    if not out and words:
        out = words[0][:max_len]
    return out


def utc_seconds(value: Any) -> str | None:
    """Truncate an ISO timestamp (or a date) to ``YYYY-MM-DDTHH:MM:SSZ`` in UTC."""
    text = _text(value)
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text += "T00:00:00+00:00"
    elif re.fullmatch(r"\d{4}-\d{2}", text):
        text += "-01T00:00:00+00:00"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def infer_date_precision(raw: Any) -> str:
    text = _text(raw)
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return "month"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return "day"
    stamp = utc_seconds(text)
    if stamp and stamp.endswith("T00:00:00Z"):
        return "day"
    return "minute"


def normalize_desk(value: Any) -> str | None:
    key = _key(value)
    if not key:
        return None
    if key in DESK_MAP:
        return DESK_MAP[key]
    for token, desk in DESK_TOKENS:
        if token == "rl":
            if "rl" in key.split("_"):
                return desk
        elif token in key:
            return desk
    return None


def normalize_development_type(value: Any) -> str | None:
    key = _key(value)
    if not key:
        return None
    if key in DEVELOPMENT_TYPE_MAP:
        return DEVELOPMENT_TYPE_MAP[key]
    for token, kind in DEVELOPMENT_TYPE_TOKENS:
        if token in key:
            return kind
    return None


def normalize_confidence(value: Any) -> str | None:
    key = _key(value)
    if not key:
        return None
    if key in CONFIDENCE_MAP:
        return CONFIDENCE_MAP[key]
    if key.startswith("confirm"):
        return "confirmed"
    if any(t in key for t in ("vendor", "unverified", "roadmap", "not_delivered", "claim", "speculat", "weak")):
        return "claimed_unverified"
    if key.startswith("strong") and not any(t in key for t in ("pending", "open", "limit", "gap", "partial")):
        return "strongly_supported"
    if any(t in key for t in ("pending", "open", "limit", "gap", "partial")):
        return "supported_with_limits"
    if key.startswith("support"):
        return "supported"
    return None


def normalize_claim_label(value: Any) -> tuple[str, str | None] | None:
    """Map an upstream claim label to (label, qualifier)."""
    raw = re.sub(r"[^A-Z0-9]+", "_", str(value or "").upper()).strip("_")
    if not raw:
        return None
    for base in CLAIM_LABELS:
        if raw == base:
            return base, None
        if raw.startswith(base + "_"):
            return base, raw[len(base) + 1:][:64] or None
    if "CLAIM" in raw:
        qualifier = raw.split("_CLAIM", 1)[0] if "_CLAIM" in raw else raw.replace("CLAIM", "").strip("_")
        return "CLAIMED", (qualifier[:64] or None)
    if "COUNTER" in raw or "DISPUT" in raw or "CONTEST" in raw:
        return "DISPUTED", (raw if raw != "DISPUTED" else None)
    if "SPECULAT" in raw or "HYPOTHES" in raw:
        return "SPECULATIVE", None
    if "INFER" in raw:
        return "INFERRED", None
    if "DEMONSTRAT" in raw or "VERIFIED" in raw:
        return "DEMONSTRATED", None
    return None


def normalize_region(value: Any) -> str | None:
    text = _text(value)
    if re.fullmatch(r"[A-Z]{2}", text):
        return "GB" if text == "UK" else text
    key = _key(text)
    if key in REGION_NAMES:
        return REGION_NAMES[key]
    if key in US_STATES:
        return "US"
    return None


def normalize_language(value: Any) -> str | None:
    text = _text(value)
    if BCP47.fullmatch(text):
        return text
    key = _key(text)
    return LANGUAGE_NAMES.get(key)


def normalize_topic(value: Any) -> str | None:
    slug = slugify(value, 80)
    return slug or None


def unique(values: Iterable[Any]) -> list[Any]:
    seen: set[Any] = set()
    out: list[Any] = []
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def valid_url(value: Any) -> str | None:
    text = _text(value)
    if not text or any(ch.isspace() for ch in text):
        return None
    parts = urlsplit(text)
    if parts.scheme not in {"http", "https"} or not parts.netloc or "." not in parts.hostname if parts.hostname else True:
        return None
    return text


def source_domain(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_primary_source(url: str) -> bool:
    domain = source_domain(url)
    return not any(domain == d or domain.endswith("." + d) for d in SECONDARY_DOMAINS)


def derive_beat(record: dict[str, Any], raw_type: Any = None) -> str:
    """Beat from the normalized desk, development type and topics (first rule wins)."""
    desk = record.get("primary_desk")
    kind = record.get("development_type")
    raw = _key(raw_type)
    if desk == "policy_geopolitics" or kind == "policy_action":
        return "policy"
    if kind in {"industry_transaction", "organizational"}:
        return "business"
    tokens: set[str] = set()
    for topic in record.get("topics") or []:
        tokens.add(topic)
        tokens.update(topic.split("-"))
    if tokens & SOCIETY_TOPIC_TOKENS:
        return "society"
    if kind in {"paper", "technical_report", "dataset_benchmark"} or "paper" in raw:
        return "research"
    return "technology"


# ---------------------------------------------------------------------------------------
# Sentences, headline and dek (derived without truncation)
# ---------------------------------------------------------------------------------------
def first_sentence(text: Any) -> str | None:
    """The first complete sentence of ``text``; None when it has no sentence end."""
    body = re.sub(r"\s+", " ", _text(text))
    if not body:
        return None
    for match in re.finditer(r"[.!?。！？](?=[\"'”’)]?(\s|$))", body):
        end = match.end()
        candidate = body[:end].rstrip()
        # Skip abbreviations ("U.S.", "e.g.") and single capitals ("J. Smith").
        tail = candidate.rsplit(" ", 1)[-1].lower()
        if tail in ABBREVIATIONS or re.fullmatch(r"\(?[a-z]\.", tail):
            continue
        rest = body[end:].lstrip()
        if rest and not re.match(r"[\"'“(\[]?[A-Z0-9一-鿿À-Þ¿¡]", rest):
            continue
        return candidate
    # CJK sentences end without a following space.
    cjk = re.match(r"(.+?[。！？])", body)
    if cjk:
        return cjk.group(1)
    return body if re.search(r"[.!?]$", body) else None


def derive_headline(title: Any) -> str | None:
    """The whole title when it already fits a headline; never a cut title."""
    text = re.sub(r"\s+", " ", _text(title))
    return text if HEADLINE_MIN <= len(text) <= HEADLINE_MAX else None


def derive_dek(summary: Any) -> str | None:
    """The first whole sentence of the summary when it fits a dek; never a cut sentence."""
    sentence = first_sentence(summary)
    if sentence and DEK_MIN <= len(sentence) <= DEK_MAX:
        return sentence
    return None


# ---------------------------------------------------------------------------------------
# Record normalization
# ---------------------------------------------------------------------------------------
def _string_list(values: Any) -> list[str]:
    out: list[str] = []
    for item in values if isinstance(values, list) else []:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = _text(item.get("text") or item.get("description") or item.get("summary"))
        else:
            text = ""
        if text:
            out.append(text)
    return out


def _int_score(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and float(value).is_integer() and 0 <= value <= 10:
        return int(value)
    return None


def normalize_record(row: Any) -> dict[str, Any]:
    """Return the record.v3 form of an upstream row, or raise Quarantine(codes)."""
    if not isinstance(row, dict):
        raise Quarantine(["NOT_AN_OBJECT"])
    codes: list[str] = []
    rid = row.get("id")
    if not isinstance(rid, str) or not PUBLIC_ID.fullmatch(rid):
        raise Quarantine(["ID_INVALID"])

    title = re.sub(r"\s+", " ", _text(row.get("title")))
    if not 8 <= len(title) <= 300:
        codes.append("TITLE_INVALID")
    summary = _text(row.get("summary"))
    if not 20 <= len(summary) <= 4000:
        codes.append("SUMMARY_INVALID")
    why = _text(row.get("why_it_matters") or row.get("why"))
    if not 20 <= len(why) <= 3000:
        codes.append("WHY_IT_MATTERS_INVALID")
    rationale = _text(row.get("importance_rationale")) or why
    if not 1 <= len(rationale) <= 3000:
        codes.append("RATIONALE_INVALID")

    primary_desk = normalize_desk(row.get("primary_desk"))
    if primary_desk is None:
        codes.append("DESK_UNKNOWN")
    desks = unique([primary_desk] + [normalize_desk(d) for d in row.get("desks") or [] if isinstance(d, str)])
    raw_type = row.get("development_type")
    development_type = normalize_development_type(raw_type)
    if development_type is None:
        codes.append("TYPE_UNKNOWN")
    confidence = normalize_confidence(row.get("confidence"))
    if confidence is None:
        codes.append("CONFIDENCE_UNKNOWN")
    evidence_class = _text(row.get("evidence_class")).upper()
    if evidence_class not in {"A", "B", "C", "D"}:
        codes.append("EVIDENCE_CLASS_INVALID")
    effective = _int_score(row.get("importance_effective_score"))
    score = _int_score(row.get("importance_score"))
    if effective is None and score is not None:
        effective = score
    if score is None and effective is not None:
        score = effective
    if effective is None:
        codes.append("IMPORTANCE_INVALID")
    tier = _text(row.get("importance_tier"))
    tier = next((t for t in TIERS if t.lower() == tier.lower()), None)
    if tier is None:
        codes.append("TIER_UNKNOWN")

    event_raw = row.get("event_at")
    event_at = utc_seconds(event_raw)
    if event_at is None:
        codes.append("EVENT_AT_INVALID")
    precision = row.get("date_precision") if row.get("date_precision") in DATE_PRECISIONS else infer_date_precision(event_raw)
    recorded_at = utc_seconds(row.get("recorded_at")) or event_at
    verified_at = utc_seconds(row.get("last_verified_at")) or recorded_at

    claims: list[dict[str, Any]] = []
    for claim in row.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        text = _text(claim.get("text"))
        mapped = normalize_claim_label(claim.get("label"))
        if not text:
            continue
        if mapped is None:
            codes.append("CLAIM_LABEL_UNKNOWN")
            continue
        if len(text) > 1500:
            codes.append("CLAIM_TOO_LONG")
            continue
        label, qualifier = mapped
        upstream_q = claim.get("qualifier")
        if isinstance(upstream_q, str) and re.fullmatch(r"[A-Z][A-Z0-9_]*", upstream_q):
            qualifier = upstream_q[:64]
        item: dict[str, Any] = {"label": label, "text": text}
        if qualifier and re.fullmatch(r"[A-Z][A-Z0-9_]*", qualifier):
            item["qualifier"] = qualifier
        claims.append(item)
    if not claims:
        codes.append("CLAIMS_MISSING")

    urls = unique(valid_url(u) for u in row.get("source_urls") or [])
    if not urls:
        codes.append("SOURCES_MISSING")

    status = _key(row.get("status")) or "active"
    status = {"retracted": "withdrawn", "withdrawn": "withdrawn", "superseded": "superseded",
              "active": "active", "developing": "developing", "published": "active"}.get(status)
    if status is None:
        codes.append("STATUS_UNKNOWN")

    kind = "event" if row.get("kind") == "event" else "development"
    scheduled_at = utc_seconds(row.get("scheduled_at"))
    if kind == "event" and scheduled_at is None:
        codes.append("SCHEDULED_AT_INVALID")

    if codes:
        raise Quarantine(codes)

    gaps = []
    for gap in row.get("evidence_gaps") or []:
        if isinstance(gap, str) and gap.strip():
            gap = {"description": gap}
        if not isinstance(gap, dict) or not _text(gap.get("description")):
            continue
        entry: dict[str, Any] = {
            "kind": _key(gap.get("kind")) if re.match(r"[a-z]", _key(gap.get("kind"))) else "other",
            "description": _text(gap.get("description")),
            "state": "closed" if gap.get("state") == "closed" else "open",
        }
        updated = utc_seconds(gap.get("updated_at"))
        if updated:
            entry["updated_at"] = updated
        gaps.append(entry)

    relationships = []
    for rel in row.get("relationships") or []:
        if not isinstance(rel, dict):
            continue
        target = rel.get("target_id")
        if not isinstance(target, str) or not PUBLIC_ID.fullmatch(target) or target == rid:
            continue
        entry = {"target_id": target, "type": rel.get("type") if rel.get("type") in RELATION_TYPES else "related"}
        text = _text(rel.get("summary"))
        if text:
            entry["summary"] = text[:600] if len(text) <= 600 else text  # schema caps at 600
            if len(text) > 600:
                entry.pop("summary")
        relationships.append(entry)

    record: dict[str, Any] = {
        "record_schema": RECORD_SCHEMA,
        "id": rid,
        "kind": kind,
        "status": status,
        "title": title,
        "summary": summary,
        "why_it_matters": why,
        "importance_rationale": rationale,
        "beat": "technology",  # replaced below
        "primary_desk": primary_desk,
        "desks": desks,
        "development_type": development_type,
        "event_at": event_at,
        "date_precision": precision,
        "recorded_at": recorded_at,
        "last_verified_at": verified_at,
        "evidence_class": evidence_class,
        "confidence": confidence,
        "importance_score": score,
        "importance_effective_score": effective,
        "importance_tier": tier,
        "claims": claims,
        "limitations": _string_list(row.get("limitations")),
        "evidence_gaps": gaps,
        "contradictory_evidence": _string_list(row.get("contradictory_evidence")),
        "organizations": unique(o.strip()[:120] for o in row.get("organizations") or [] if isinstance(o, str) and o.strip()),
        "topics": unique(normalize_topic(t) for t in row.get("topics") or [] if isinstance(t, str)),
        "regions": unique(normalize_region(r) for r in row.get("regions") or []),
        "source_languages": unique(normalize_language(l) for l in row.get("source_languages") or []) or ["und"],
        "source_urls": urls,
    }
    if isinstance(row.get("importance_scale_version"), int) and row["importance_scale_version"] >= 1:
        record["importance_scale_version"] = row["importance_scale_version"]
    record["beat"] = row["beat"] if row.get("beat") in BEATS else derive_beat(record, raw_type)
    if kind == "event":
        record["scheduled_at"] = scheduled_at
    headline = re.sub(r"\s+", " ", _text(row.get("headline")))
    if HEADLINE_MIN <= len(headline) <= HEADLINE_MAX:
        record["headline"] = headline
    dek = re.sub(r"\s+", " ", _text(row.get("dek")))
    if DEK_MIN <= len(dek) <= DEK_MAX:
        record["dek"] = dek
    technical = row.get("technical")
    if isinstance(technical, dict):
        tech = {str(k): v.strip() for k, v in technical.items() if isinstance(v, str) and v.strip()}
        if tech:
            record["technical"] = tech
    if relationships:
        record["relationships"] = relationships
    dedup = _text(row.get("dedup_key"))
    if re.fullmatch(r"[a-z0-9-]+\|[a-z0-9_]+\|\d{4}-\d{2}-\d{2}", dedup):
        record["dedup_key"] = dedup
    editions = [e for e in row.get("editions") or [] if isinstance(e, str)]
    if editions:
        record["editions"] = editions
    sources = []
    for src in row.get("sources") or []:
        if isinstance(src, dict) and valid_url(src.get("url")):
            entry = {"url": src["url"], "primary": bool(src.get("primary"))}
            if src.get("kind") in {"paper", "company", "government", "regulator", "court", "filing", "news",
                                   "repository", "dataset", "blog", "other"}:
                entry["kind"] = src["kind"]
            checked = utc_seconds(src.get("http_checked_at"))
            if checked:
                entry["http_checked_at"] = checked
            sources.append(entry)
    if sources:
        record["sources"] = sources
    if status in {"withdrawn", "superseded"}:
        record["withdrawal"] = normalize_withdrawal(row.get("withdrawal"), status, verified_at)
    return record


GENERIC_WITHDRAWAL_NOTE = "Withdrawn by the research feed. No further public detail was provided with the withdrawal."


def normalize_withdrawal(block: Any, status: str, fallback_at: str) -> dict[str, Any]:
    block = block if isinstance(block, dict) else {}
    note = _text(block.get("note"))
    out: dict[str, Any] = {
        "at": utc_seconds(block.get("at")) or fallback_at,
        "reason_code": block.get("reason_code") if block.get("reason_code") in WITHDRAWAL_REASONS else (
            "DUPLICATE" if status == "superseded" else "UPSTREAM_RETRACTION"),
        "note": note if 20 <= len(note) <= 600 else GENERIC_WITHDRAWAL_NOTE,
    }
    target = block.get("superseded_by")
    if isinstance(target, str) and PUBLIC_ID.fullmatch(target):
        out["superseded_by"] = target
    return out


def normalize_rows(rows: Iterable[Any]) -> tuple[list[dict[str, Any]], list[tuple[str, list[str]]]]:
    """Normalize every row; returns (records, [(id or '-', codes)]) for the quarantine."""
    records: list[dict[str, Any]] = []
    quarantined: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    for row in rows:
        rid = row.get("id") if isinstance(row, dict) and isinstance(row.get("id"), str) else "-"
        try:
            record = normalize_record(row)
        except Quarantine as exc:
            quarantined.append((rid if PUBLIC_ID.fullmatch(rid or "") else "-", exc.codes))
            continue
        if record["id"] in seen:
            quarantined.append((record["id"], ["DUPLICATE_ID"]))
            continue
        seen.add(record["id"])
        records.append(record)
    return records, quarantined


def read_jsonl(path: Path) -> list[Any]:
    rows: list[Any] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"id": f"-line-{number}"})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "normalize"):
        p = sub.add_parser(name)
        p.add_argument("corpus", type=Path, help="corpus directory or developments .jsonl file")
        if name == "normalize":
            p.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    source = args.corpus / "data" / "developments.jsonl" if args.corpus.is_dir() else args.corpus
    try:
        rows = read_jsonl(source)
    except OSError as exc:
        print(f"USAGE unreadable corpus: {type(exc).__name__}", file=sys.stderr)
        return 2
    records, quarantined = normalize_rows(rows)
    for rid, codes in quarantined:
        print(f"QUARANTINE {rid} {','.join(codes)}")
    if args.command == "normalize":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    print(f"taxonomy OK records={len(records)} quarantined={len(quarantined)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
