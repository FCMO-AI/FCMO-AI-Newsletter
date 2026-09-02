#!/usr/bin/env python3
"""One-shot authoring helper for complete FCMO curated locale packs.

This script is intentionally NOT part of the publication runtime. It uses GitHub Models
only during editorial authoring to produce source-controlled candidate translations.
The committed output is subsequently validated by the normal fail-closed publication
pipeline; the public site never calls a translation or generative endpoint.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

MODEL = os.environ.get("FCMO_I18N_AUTHOR_MODEL", "openai/gpt-4.1")
ENDPOINT = "https://models.github.ai/inference/chat/completions"
LOCALES = {
    "es-419": "natural professional Latin American Spanish suitable for a serious Mexican/Latin-American technology publication",
    "zh-Hans": "natural professional Simplified Chinese suitable for a serious mainland-Chinese technology/research publication",
}
DETAIL_FIELDS = (
    "title", "summary", "why_it_matters", "importance_rationale",
    "claims", "contradictory_evidence", "engineering_implications",
    "research_implications", "policy_implications", "limitations",
    "evidence_gaps", "relationships", "technical",
)
ROOT_UI_PAGES = (
    "about.html", "archive.html", "corrections.html", "disclaimer.html",
    "feeds.html", "license.html", "organizations.html", "privacy.html",
    "search.html", "topics.html",
)
DYNAMIC_UI_PHRASES = {
    "Loading index…", "Search index unavailable", "No records match these filters.",
    "records", "of", "published", "draft", "verified", "development", "paper",
    "active", "open", "related", "confirmed", "strongly_supported", "supported",
    "unconfirmed", "Field-shifting", "Very major", "Major", "Notable",
    "DEMONSTRATED", "CLAIMED", "INFERRED", "SPECULATIVE",
    "Evidence claims", "Technical record", "Mechanism", "Demonstrated result",
    "Publisher claim", "Strongest baseline", "Regime", "Implementation",
    "Compute / cost", "Novelty", "Reproducibility", "Limitations / contrary evidence",
    "Open evidence gaps", "Relationships", "No structured relationships recorded.",
    "Sources", "Importance", "Impact", "Evidence", "Confidence", "Status",
    "Research implications", "Engineering implications", "Policy implications",
    "Contradictory evidence", "Limitations", "Open evidence gaps",
}


def _request(prompt: str, token: str, max_tokens: int = 24000) -> Any:
    payload = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the FCMO AI Newsletter localization editor. Translate faithfully and natively. "
                    "Preserve every number, percentage, model/version name, benchmark name, organization/proper noun, "
                    "stable identifier, URL, evidence strength, caveat, uncertainty, and distinction between demonstrated, "
                    "claimed, inferred, speculative, and editorial interpretation. Do not strengthen claims. Do not summarize, "
                    "omit, merge, split, or add facts. Return valid JSON only and preserve the exact JSON shape, keys, list lengths, "
                    "and ordering of the supplied object. Translate natural-language string values; leave machine identifiers and URLs unchanged."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        method="POST",
    )
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.load(resp)
            return json.loads(body["choices"][0]["message"]["content"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (408, 409, 429, 500, 502, 503, 504):
                detail = exc.read().decode("utf-8", "replace")
                raise RuntimeError(f"GitHub Models authoring request failed: HTTP {exc.code}: {detail}") from exc
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"GitHub Models authoring request failed after retries: {last}")


def _extract_detail(brief_payload: dict[str, Any]) -> dict[str, Any]:
    brief = brief_payload.get("brief", brief_payload)
    out: dict[str, Any] = {}
    for field in DETAIL_FIELDS:
        if field not in brief:
            continue
        value = brief[field]
        if field == "claims":
            out[field] = [{"text": row.get("text", "")} for row in value]
        elif field == "evidence_gaps":
            out[field] = [{"description": row.get("description", "")} for row in value]
        elif field == "relationships":
            out[field] = [{"summary": row.get("summary", "")} for row in value if row.get("summary")]
        elif field == "technical":
            out[field] = {k: v for k, v in value.items() if isinstance(v, str) and v.strip()}
        else:
            out[field] = value
    return out


def _shape(source: Any) -> Any:
    if isinstance(source, dict):
        return {k: _shape(v) for k, v in source.items()}
    if isinstance(source, list):
        return [_shape(v) for v in source]
    if isinstance(source, str):
        return "string"
    return type(source).__name__


def _validate_translation(source: Any, translated: Any, path: str = "") -> None:
    if isinstance(source, dict):
        if not isinstance(translated, dict) or list(translated) != list(source):
            raise ValueError(f"shape/key mismatch at {path or '<root>'}")
        for key in source:
            _validate_translation(source[key], translated[key], f"{path}.{key}" if path else key)
        return
    if isinstance(source, list):
        if not isinstance(translated, list) or len(translated) != len(source):
            raise ValueError(f"list-length mismatch at {path}")
        for idx, (a, b) in enumerate(zip(source, translated)):
            _validate_translation(a, b, f"{path}[{idx}]")
        return
    if isinstance(source, str):
        if not isinstance(translated, str) or not translated.strip():
            raise ValueError(f"missing translated string at {path}")
        return
    if type(source) is not type(translated) or source != translated:
        raise ValueError(f"non-string value changed at {path}: {source!r} -> {translated!r}")


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.text: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self.skip += 1
        for key, value in attrs:
            if key in ("placeholder", "title", "aria-label", "label") and value and re.search(r"[A-Za-z]", value):
                self.text.add(" ".join(value.split()))

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        value = " ".join(data.split())
        if value and re.search(r"[A-Za-z]", value) and not re.fullmatch(r"https?://\S+", value):
            self.text.add(value)


def _ui_source(root: Path) -> list[str]:
    values = set(DYNAMIC_UI_PHRASES)
    for rel in ROOT_UI_PAGES:
        path = root / rel
        if not path.is_file():
            continue
        parser = VisibleText()
        parser.feed(path.read_text(encoding="utf-8"))
        values.update(parser.text)
    # Brand/proper names and machine-facing labels need not be translated.
    values.discard("FCMO AI Newsletter")
    values = {v for v in values if not re.fullmatch(r"[A-Z0-9_.+:/ -]+", v)}
    return sorted(values, key=lambda s: (s.lower(), s))


def _translate_ui(values: list[str], locale: str, language: str, token: str) -> dict[str, str]:
    # Chunk to keep responses robust and reviewable.
    result: dict[str, str] = {}
    for start in range(0, len(values), 70):
        chunk = values[start:start + 70]
        source = {text: text for text in chunk}
        prompt = (
            f"Translate the VALUES of this UI/publication-copy JSON object into {language}. "
            "Keep the English keys exactly unchanged. Preserve FCMO AI Newsletter, model names, benchmark names, filenames, URLs, dates and code identifiers when embedded. "
            f"Object:\n{json.dumps(source, ensure_ascii=False)}"
        )
        translated = _request(prompt, token, max_tokens=12000)
        if set(translated) != set(source):
            raise ValueError(f"{locale}: UI translation key mismatch")
        for key, value in translated.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{locale}: empty UI translation for {key!r}")
            result[key] = value
    return result


def main() -> None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN/GITHUB_TOKEN is required")
    publish = Path(os.environ.get("FCMO_PUBLISH_ROOT", "publish"))
    site = Path(os.environ.get("FCMO_SITE_ROOT", "site"))
    briefs_dir = publish / "data" / "briefs"
    brief_paths = sorted(briefs_dir.glob("FCMO-*.json"))
    if not brief_paths:
        raise SystemExit(f"no canonical briefs found at {briefs_dir}")

    sources: dict[str, dict[str, Any]] = {}
    for path in brief_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rid = payload.get("record", {}).get("id") or payload.get("brief", {}).get("id") or path.stem
        sources[rid] = _extract_detail(payload)

    ui_values = _ui_source(publish)
    ordered_ids = sorted(sources)
    for locale, language in LOCALES.items():
        out_dir = site / "data" / "i18n" / locale
        out_dir.mkdir(parents=True, exist_ok=True)
        translated_records: dict[str, Any] = {}
        for idx, rid in enumerate(ordered_ids, 1):
            source = sources[rid]
            prompt = (
                f"Translate this complete FCMO AI Newsletter public dossier excerpt into {language}. "
                "Return the same JSON object shape with all information preserved. "
                f"Stable record ID for context only: {rid}.\nSOURCE JSON:\n{json.dumps(source, ensure_ascii=False)}"
            )
            translated = _request(prompt, token)
            _validate_translation(source, translated)
            translated_records[rid] = translated
            print(f"{locale}: translated {idx}/{len(ordered_ids)} {rid}", flush=True)

        groups = [ordered_ids[i:i + 6] for i in range(0, len(ordered_ids), 6)]
        for number, ids in enumerate(groups, 1):
            payload = {
                "schema": "fcmo-curated-detail-part-v1",
                "locale": locale,
                "canonical_locale": "en",
                "records": {rid: translated_records[rid] for rid in ids},
            }
            (out_dir / f"detail-{number:02d}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

        ui = _translate_ui(ui_values, locale, language, token)
        (out_dir / "ui-extra.json").write_text(
            json.dumps({"schema": "fcmo-curated-ui-extra-v1", "locale": locale, "ui": ui}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{locale}: wrote {len(translated_records)} complete dossier translations and {len(ui)} UI phrases", flush=True)


if __name__ == "__main__":
    main()
