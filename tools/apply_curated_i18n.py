#!/usr/bin/env python3
"""Apply FCMO AI Newsletter curated EN/ES/ZH localization to an assembled public tree.

English remains canonical. Spanish and Simplified Chinese are committed, reviewable
locale packs. No network translation provider or runtime generative fallback exists.
"""
from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

SUPPORTED = ("en", "es-419", "zh-Hans")
CURATED = ("es-419", "zh-Hans")
REQUIRED_FIELDS = ("title", "summary", "why_it_matters")
BUNDLE_MARKER = 'id="fcmo-i18n-data"'
SCRIPT_MARKER = 'assets/curated-i18n.js'
STYLE_MARKER = 'assets/curated-i18n.css'
TRANSLATION_ENDPOINT_MARKERS = (
    "translate.googleapis.com", "googleapis.com/language/translate", "api.deepl.com",
    "api.cognitive.microsofttranslator.com", "api.openai.com", "api.anthropic.com",
)
UI_ATTRIBUTE_NAMES = {"aria-label", "placeholder", "title", "label"}
LEGAL_ATTRIBUTE = ("data-fcmo-legal", "canonical")


class _VisibleIndexParser(HTMLParser):
    """Collect user-facing HTML text while ignoring executable/data blocks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored = 0
        self.text: list[str] = []
        self.attributes: list[str] = []
        self.inline_scripts: list[str] = []
        self._script_attrs: dict[str, str] | None = None
        self._script_buffer: list[str] = []
        self._element_stack: list[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() in {"script", "style"}:
            self._ignored += 1
            if tag.lower() == "script":
                self._script_attrs = attrs_map
                self._script_buffer = []
            return
        is_legal = attrs_map.get(LEGAL_ATTRIBUTE[0]) == LEGAL_ATTRIBUTE[1]
        self._element_stack.append((tag.lower(), is_legal))
        if self._ignored:
            return
        if any(legal for _, legal in self._element_stack):
            return
        for key, value in attrs:
            if key.lower() in UI_ATTRIBUTE_NAMES and value:
                self.attributes.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() not in {"script", "style"} or not self._ignored:
            for index in range(len(self._element_stack) - 1, -1, -1):
                if self._element_stack[index][0] == tag.lower():
                    del self._element_stack[index:]
                    break
            return
        if tag.lower() == "script" and self._script_attrs is not None:
            attrs = self._script_attrs
            if not attrs.get("src") and attrs.get("type") not in {"application/json", "application/ld+json"}:
                self.inline_scripts.append("".join(self._script_buffer))
            self._script_attrs = None
            self._script_buffer = []
        self._ignored -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored:
            if self._script_attrs is not None:
                self._script_buffer.append(data)
            return
        if any(legal for _, legal in self._element_stack):
            return
        self.text.append(data)


def _clean_ui_text(value: str) -> str:
    return " ".join(value.split()).strip()


def _visible_ui_strings(index_text: str, catalog_keys: set[str]) -> set[str]:
    """Extract visible UI phrases from the assembled index.

    The final index is an app shell: its initial HTML contains the persistent
    chrome, while route views are templates in the inline application script.
    Catalog keys found in that script are therefore included as UI candidates;
    embedded JSON is deliberately excluded so a story's editorial prose is not
    mistaken for a UI phrase.  The count-bearing issue-stamp phrase is kept in
    its source form, without baking the live number into the catalogue key.
    """
    parser = _VisibleIndexParser()
    parser.feed(index_text)
    visible = {
        _clean_ui_text(value)
        for value in [*parser.text, *parser.attributes]
        if _clean_ui_text(value) in catalog_keys
    }
    inline_source = "\n".join(parser.inline_scripts)
    visible.update(key for key in catalog_keys if key and key in inline_source)

    dynamic_issue_phrase = "public briefs / complete corpus inside"
    if re.search(r"(?:\$\{[^}]+\}|<N>|\d+)\s+" + re.escape(dynamic_issue_phrase), inline_source):
        visible.add(dynamic_issue_phrase)
    return visible


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_editorial(index_text: str) -> dict[str, dict[str, str]]:
    match = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', index_text, re.S)
    if not match:
        raise ValueError("index is missing embedded fcmo-data corpus")
    data = json.loads(match.group(1))
    records = data.get("records") or []
    if not records:
        raise ValueError("canonical corpus contains no news records")
    editorial: dict[str, dict[str, str]] = {}
    for row in records:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid.strip():
            raise ValueError("canonical corpus contains a record without a stable id")
        if rid in editorial:
            raise ValueError(f"canonical corpus contains duplicate record id: {rid}")
        missing = [field for field in REQUIRED_FIELDS if not isinstance(row.get(field), str) or not row[field].strip()]
        if missing:
            raise ValueError(f"canonical record {rid} is missing required editorial fields: {', '.join(missing)}")
        editorial[rid] = {field: row[field] for field in REQUIRED_FIELDS}
    return editorial


def _canonical_digest(canonical: dict[str, dict[str, str]]) -> str:
    return sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def _load_pack(target: Path, locale: str) -> dict:
    # Locale packs are deliberately split into small reviewable source files so a
    # story translation can be audited without wading through a monolithic blob.
    locale_dir = target / "data" / "i18n" / locale
    ui_path = locale_dir / "ui.json"
    parts = sorted(locale_dir.glob("part-*.json")) if locale_dir.is_dir() else []
    if not ui_path.is_file() or not parts:
        raise ValueError(f"missing curated locale pack directory: {locale_dir.relative_to(target)}")
    ui = json.loads(ui_path.read_text(encoding="utf-8"))
    records: dict[str, dict[str, str]] = {}
    for path in parts:
        part = json.loads(path.read_text(encoding="utf-8"))
        if part.get("schema") != "fcmo-curated-locale-part-v1" or part.get("locale") != locale:
            raise ValueError(f"{path.relative_to(target)}: invalid locale part metadata")
        if part.get("canonical_source_sha256") != ui.get("canonical_source_sha256"):
            raise ValueError(f"{path.relative_to(target)}: canonical source hash drift")
        overlap = set(records) & set(part.get("records") or {})
        if overlap:
            raise ValueError(f"{path.relative_to(target)}: duplicate record IDs {sorted(overlap)}")
        records.update(part.get("records") or {})
    return {
        "schema": "fcmo-curated-locale-v1",
        "locale": locale,
        "language_name": "Español (Latinoamérica)" if locale == "es-419" else "简体中文",
        "canonical_locale": "en",
        "curation": ui.get("curation") or {},
        "canonical_record_count": ui.get("canonical_record_count"),
        "canonical_source_sha256": ui.get("canonical_source_sha256"),
        "records": records,
        "ui": ui.get("ui") or {},
    }


def validate_curated_i18n(target: Path, canonical_index_sha256: str | None = None) -> dict:
    index = target / "index.html"
    text = index.read_text(encoding="utf-8")
    canonical = _canonical_editorial(text)
    expected_ids = set(canonical)
    canonical_count = len(expected_ids)
    digest = _canonical_digest(canonical)
    errors: list[str] = []
    packs: dict[str, dict] = {}

    for locale in CURATED:
        try:
            pack = _load_pack(target, locale)
            packs[locale] = pack
        except Exception as exc:
            errors.append(str(exc)); continue
        if pack.get("schema") != "fcmo-curated-locale-v1":
            errors.append(f"{locale}: wrong locale schema")
        if pack.get("locale") != locale or pack.get("canonical_locale") != "en":
            errors.append(f"{locale}: locale/canonical metadata mismatch")
        if pack.get("curation", {}).get("runtime_machine_translation") is not False:
            errors.append(f"{locale}: runtime translation must be explicitly false")
        if pack.get("curation", {}).get("human_reviewed") is not False:
            errors.append(f"{locale}: pack must not claim human review")
        if pack.get("canonical_record_count") != canonical_count:
            errors.append(
                f"{locale}: canonical_record_count metadata is {pack.get('canonical_record_count')!r}, "
                f"expected {canonical_count}"
            )
        if pack.get("canonical_source_sha256") != digest:
            errors.append(f"{locale}: canonical editorial source hash mismatch")
        rows = pack.get("records") or {}
        if set(rows) != expected_ids:
            missing = sorted(expected_ids - set(rows))
            extra = sorted(set(rows) - expected_ids)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if extra:
                detail.append(f"extra {extra}")
            errors.append(f"{locale}: record IDs do not exactly match canonical corpus ({'; '.join(detail)})")
        for rid in sorted(expected_ids & set(rows)):
            for field in REQUIRED_FIELDS:
                value = rows[rid].get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{locale}: {rid}.{field} missing")
                elif value.strip() == canonical[rid][field].strip():
                    errors.append(f"{locale}: {rid}.{field} is unchanged canonical English")
        if not isinstance(pack.get("ui"), dict) or len(pack["ui"]) < 40:
            errors.append(f"{locale}: UI catalogue is unexpectedly incomplete")

    if len(packs) == len(CURATED):
        ui_catalogs = {locale: set(pack["ui"]) for locale, pack in packs.items()}
        catalog_keys = set().union(*ui_catalogs.values())
        visible_ui: set[str] = set()
        for page in sorted(target.rglob("*.html")):
            visible_ui.update(_visible_ui_strings(page.read_text(encoding="utf-8"), catalog_keys))
        for locale, catalog in ui_catalogs.items():
            missing = sorted(
                phrase
                for phrase in visible_ui
                if phrase not in catalog
                and not (
                    phrase == "public briefs / complete corpus inside"
                    and "<N> public briefs / complete corpus inside" in catalog
                )
            )
            if missing:
                errors.append(f"{locale}: visible UI strings missing from ui catalogue: {missing}")

    for marker in TRANSLATION_ENDPOINT_MARKERS:
        for path in [target / "assets" / "curated-i18n.js", *(target / "data" / "i18n").rglob("*.json")]:
            if path.is_file() and marker in path.read_text(encoding="utf-8").lower():
                errors.append(f"runtime translation/provider endpoint detected in {path.relative_to(target)}: {marker}")

    localized = BUNDLE_MARKER in text and SCRIPT_MARKER in text and STYLE_MARKER in text
    if localized:
        manifest_path = target / "data" / "i18n" / "manifest.json"
        if not manifest_path.is_file():
            errors.append("localized index exists but data/i18n/manifest.json is missing")
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("supported_locales") != list(SUPPORTED):
                errors.append("i18n manifest must expose exactly en, es-419, zh-Hans")
            if manifest.get("canonical_record_count") != canonical_count:
                errors.append("i18n manifest canonical record count mismatch")
            if manifest.get("canonical_editorial_sha256") != digest:
                errors.append("i18n manifest canonical editorial hash mismatch")
            if canonical_index_sha256 and manifest.get("canonical_index_sha256") != canonical_index_sha256:
                errors.append("i18n manifest canonical index hash mismatch")
            current_index_hash = sha256(index.read_bytes())
            if manifest.get("localized_index_sha256") != current_index_hash:
                errors.append("i18n manifest localized index hash mismatch")

    if errors:
        raise ValueError("curated localization validation failed:\n- " + "\n- ".join(errors))
    return {"records": canonical_count, "canonical_editorial_sha256": digest, "packs": packs}


def _inject_runtime(page_text: str, canonical_tag: str | None, encoded_bundle: str, asset_prefix: str) -> str:
    """Inject the shared runtime into an index or a one-level static page."""
    style_marker = 'data-fcmo-i18n="style"'
    runtime_marker = 'data-fcmo-i18n="runtime"'
    if BUNDLE_MARKER in page_text:
        if style_marker not in page_text or runtime_marker not in page_text:
            raise ValueError("page contains a partial curated localization runtime")
        return page_text

    style_tag = (
        f'<link rel="stylesheet" href="{asset_prefix}assets/curated-i18n.css" '
        'data-fcmo-i18n="style">'
    )
    payload = (
        f'<script id="fcmo-i18n-data" type="application/json">{encoded_bundle}</script>'
        f'<script src="{asset_prefix}assets/curated-i18n.js" data-fcmo-i18n="runtime"></script>'
    )
    localized = page_text
    if style_marker not in localized:
        localized, count = re.subn(r"</head>", style_tag + "</head>", localized, count=1, flags=re.I)
        if count != 1:
            raise ValueError("unable to locate </head> for deterministic localization injection")

    data_match = re.search(r'<script id="fcmo-data" type="application/json">.*?</script>', localized, re.S)
    if data_match:
        localized = localized[:data_match.end()] + payload + localized[data_match.end():]
    else:
        body_match = re.search(r"</body>", localized, re.I)
        if not body_match:
            raise ValueError("unable to locate </body> for deterministic localization injection")
        prefix = canonical_tag or ""
        localized = localized[:body_match.start()] + prefix + payload + localized[body_match.start():]
    return localized


def apply_curated_i18n(target: Path, canonical_index_sha256: str) -> None:
    index = target / "index.html"
    original = index.read_text(encoding="utf-8")
    if BUNDLE_MARKER in original:
        validate_curated_i18n(target, canonical_index_sha256)
        return
    if sha256(index.read_bytes()) != canonical_index_sha256:
        raise ValueError("refusing to localize an index that is not the frozen canonical English release")

    result = validate_curated_i18n(target)
    bundle = {
        "schema": "fcmo-curated-i18n-bundle-v1",
        "canonical_locale": "en",
        "supported_locales": list(SUPPORTED),
        "curated_locales": list(CURATED),
        "packs": {locale: result["packs"][locale] for locale in CURATED},
    }
    match = re.search(r'(<script id="fcmo-data" type="application/json">.*?</script>)', original, re.S)
    if not match:
        raise ValueError("unable to locate canonical data block for deterministic injection")
    encoded = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    localized = _inject_runtime(original, match.group(1), encoded, "")
    index.write_text(localized, encoding="utf-8", newline="\n")

    stub_bundle = {
        "schema": bundle["schema"],
        "canonical_locale": bundle["canonical_locale"],
        "supported_locales": bundle["supported_locales"],
        "curated_locales": bundle["curated_locales"],
        "packs": {
            locale: {"ui": result["packs"][locale]["ui"]}
            for locale in CURATED
        },
    }
    encoded_stub = json.dumps(stub_bundle, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    for directory in (target / "developments", target / "editions"):
        if not directory.is_dir():
            continue
        for page in sorted(directory.glob("*.html")):
            page_text = page.read_text(encoding="utf-8")
            page_localized = _inject_runtime(page_text, None, encoded_stub, "../")
            if page_localized != page_text:
                page.write_text(page_localized, encoding="utf-8", newline="\n")

    for page in sorted(target.glob("*.html")):
        if page.name == "index.html":
            continue
        page_text = page.read_text(encoding="utf-8")
        page_localized = _inject_runtime(page_text, match.group(1), encoded, "")
        if page_localized != page_text:
            page.write_text(page_localized, encoding="utf-8", newline="\n")

    manifest = {
        "schema": "fcmo-curated-i18n-manifest-v1",
        "canonical_locale": "en",
        "supported_locales": list(SUPPORTED),
        "curated_locales": list(CURATED),
        "canonical_record_count": result["records"],
        "canonical_index_sha256": canonical_index_sha256,
        "canonical_editorial_sha256": result["canonical_editorial_sha256"],
        "localized_index_sha256": sha256(index.read_bytes()),
        "runtime_machine_translation": False,
        "human_review_claim": False,
        "locale_resolution": ["?lang=", "saved manual selection", "navigator.languages", "en fallback"],
    }
    (target / "data" / "i18n" / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # The frozen release builder writes build-manifest.json before localization. Refresh it
    # after adding the curated runtime so the published integrity ledger describes the
    # actual bytes that GitHub Pages will serve.
    build_path = target / "build-manifest.json"
    if build_path.is_file():
        build = json.loads(build_path.read_text(encoding="utf-8"))
        entries = {}
        for path in sorted(p for p in target.rglob("*") if p.is_file()):
            rel = path.relative_to(target).as_posix()
            if rel == "build-manifest.json":
                continue
            entries[rel] = sha256(path.read_bytes())
        build["files"] = entries
        build["localization"] = {
            "schema": manifest["schema"],
            "supported_locales": manifest["supported_locales"],
            "canonical_index_sha256": manifest["canonical_index_sha256"],
            "localized_index_sha256": manifest["localized_index_sha256"],
        }
        build_path.write_text(json.dumps(build, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    validate_curated_i18n(target, canonical_index_sha256)


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if len(sys.argv) > 2:
        canonical_hash = sys.argv[2]
    else:
        localized_manifest = root / "data" / "i18n" / "manifest.json"
        if BUNDLE_MARKER in (root / "index.html").read_text(encoding="utf-8") and localized_manifest.is_file():
            canonical_hash = json.loads(localized_manifest.read_text(encoding="utf-8"))["canonical_index_sha256"]
        else:
            canonical_hash = sha256((root / "index.html").read_bytes())
    apply_curated_i18n(root, canonical_hash)
    print(f"Curated FCMO localization applied: {', '.join(SUPPORTED)}")
