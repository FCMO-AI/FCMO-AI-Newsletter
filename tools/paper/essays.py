"""Load, validate and render the source-controlled FCMO human editorial tree."""
from __future__ import annotations

from datetime import datetime
import json
import importlib
import importlib.util
from pathlib import Path
import re
import shutil
from typing import Any
from urllib.parse import urlsplit

from tests.harness.validate import Validator
from . import essay_doc
from .routes import absolute, href, issue_path, piece_path

ROOT = Path(__file__).resolve().parents[2]
LOCALES = ("en", "es-419", "zh-Hans")
PREFIXES = {"en": "", "es-419": "es/", "zh-Hans": "zh/"}
LOCALE_WORDS = {
    "en": {"by": "By", "updated": "Updated", "pending": "This essay is not yet available in English.", "withdrawn": "Withdrawn", "withdrawal_note": "Withdrawal note"},
    "es-419": {"by": "Por", "updated": "Actualizado", "pending": "Este ensayo aún no está disponible en español.", "withdrawn": "Retirado", "withdrawal_note": "Aviso de retiro"},
    "zh-Hans": {"by": "作者", "updated": "更新", "pending": "此文尚未提供简体中文版本。", "withdrawn": "已撤回", "withdrawal_note": "撤回说明"},
}
MACHINE_DISCLOSURE = {
    "en": "This language version was prepared automatically and has not been reviewed by a person.",
    "es-419": "Esta versión se preparó automáticamente y todavía no la revisó una persona.",
    "zh-Hans": "此语言版本由机器准备，尚未经过人工审核。",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(path: Path, schema_name: str, value: Any) -> None:
    schema = _load(ROOT / "contracts" / schema_name)
    errors = Validator(schema).errors(value)
    if errors:
        raise ValueError(f"{path}: " + "; ".join(errors[:5]))


def load_piece(directory: Path) -> dict:
    piece_path = directory / "piece.json"
    piece = _load(piece_path)
    _validate(piece_path, "piece.v1.schema.json", piece)
    if directory.name != piece["slug"]:
        raise ValueError(f"{piece_path}: directory does not match slug")
    docs, sources, figures = {}, _load(directory / "sources.json"), _load(directory / "figures.json")
    provenance_path = directory / "provenance.json"
    provenance = _load(provenance_path)
    if not isinstance(provenance, dict) or set(provenance) - set(LOCALES):
        raise ValueError(f"{directory}: invalid provenance locales")
    if not isinstance(sources, list) or not isinstance(figures, dict):
        raise ValueError(f"{directory}: sources must be an array and figures an object")
    if any(not isinstance(row, dict) for row in sources):
        raise ValueError(f"{directory}: each source must be an object")
    source_keys = [row.get("key") for row in sources if isinstance(row, dict)]
    if len(source_keys) != len(set(source_keys)):
        raise ValueError(f"{directory}: duplicate source key")
    for source in sources:
        allowed = {"key", "title", "author", "publisher", "date", "url", "accessed", "locator", "evidence_class", "note"}
        if set(source) - allowed or not {"key", "title", "author", "publisher", "date", "url", "accessed"}.issubset(source):
            raise ValueError(f"{directory}: source has missing or unknown fields")
        parts = urlsplit(source.get("url", ""))
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            raise ValueError(f"{directory}: source URL must use https")
    for fig_id, fig in figures.items():
        allowed = {"file", "width", "height", "credit", "licence", "licence_url", "source_page", "alt", "caption"}
        required = {"file", "width", "height", "credit", "licence", "alt", "caption"}
        if not isinstance(fig, dict) or set(fig) - allowed or not required.issubset(fig):
            raise ValueError(f"{directory}: figure {fig_id} has missing or unknown fields")
        rel = fig.get("file", "") if isinstance(fig, dict) else ""
        if not re.fullmatch(r"figures/[A-Za-z0-9-]+\.webp", rel):
            raise ValueError(f"{directory}: figure {fig_id} has an unsafe or unsupported file path")
        if not isinstance(fig["width"], int) or not isinstance(fig["height"], int) or min(fig["width"], fig["height"]) < 1 or max(fig["width"], fig["height"]) > 8000:
            raise ValueError(f"{directory}: figure {fig_id} has invalid dimensions")
        if not isinstance(fig["credit"], str) or not fig["credit"].strip() or not isinstance(fig["licence"], str) or not fig["licence"].strip():
            raise ValueError(f"{directory}: figure {fig_id} requires credit and licence")
        for field in ("alt", "caption"):
            if not isinstance(fig[field], dict) or set(fig[field]) - set(LOCALES):
                raise ValueError(f"{directory}: figure {fig_id} has invalid {field} locales")
        candidate = directory / rel
        if directory.resolve() not in candidate.resolve().parents or not candidate.is_file():
            raise ValueError(f"{directory}: figure {fig_id} file is missing or escapes the piece directory")
    for locale in LOCALES:
        doc_path = directory / f"doc.{locale}.json"
        if not doc_path.exists():
            if piece["locales"][locale] == "ready":
                raise ValueError(f"{doc_path}: ready locale has no document")
            continue
        doc = _load(doc_path)
        _validate(doc_path, "essay-doc.v1.schema.json", doc)
        if doc["locale"] != locale:
            raise ValueError(f"{doc_path}: locale does not match filename")
        docs[locale] = doc
    if piece["status"] == "published" and piece["source_locale"] not in docs:
        raise ValueError(f"{directory}: source locale document is missing")
    if piece["status"] == "published" and piece["locales"][piece["source_locale"]] != "ready":
        raise ValueError(f"{directory}: source locale must be ready before publication")
    if piece["hero"] is not None and piece["hero"] not in figures:
        raise ValueError(f"{directory}: hero references missing figure {piece['hero']}")
    ids_by_locale = {loc: [block["id"] for block in doc["blocks"]] for loc, doc in docs.items()}
    source_ids = ids_by_locale.get(piece["source_locale"], [])
    source_fn_ids = set(docs.get(piece["source_locale"], {}).get("footnotes", {}))
    source_structure = _structure(docs.get(piece["source_locale"], {}))
    source_tokens = _tokens(docs.get(piece["source_locale"], {}))
    for locale, doc in docs.items():
        ids = ids_by_locale[locale]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{directory}: duplicate block id in {locale}")
        if ids != source_ids:
            raise ValueError(f"{directory}: block id mismatch in {locale}")
        row = provenance.get(locale, {})
        if not isinstance(row, dict) or set(row) - {"origin", "human_reviewed", "reviewer", "at", "model", "source_locale"}:
            raise ValueError(f"{directory}: invalid provenance fields in {locale}")
        if row.get("origin") not in {"human_authored", "human_translated", "agent_draft_human_edited", "agent_draft"} or not isinstance(row.get("human_reviewed"), bool):
            raise ValueError(f"{directory}: invalid provenance in {locale}")
        if piece["locales"][locale] == "ready" and row["origin"] != "agent_draft" and row["human_reviewed"] is not True:
            raise ValueError(f"{directory}: ready {locale} has not been human-reviewed")
        if row["human_reviewed"] is True and not str(row.get("reviewer", "")).strip():
            raise ValueError(f"{directory}: human review needs a named reviewer")
        fn_ids = set(doc.get("footnotes", {}))
        if fn_ids != source_fn_ids:
            raise ValueError(f"{directory}: footnote id mismatch in {locale}")
        if _structure(doc) != source_structure:
            raise ValueError(f"{directory}: footnote, citation or figure structure mismatch in {locale}")
        if _tokens(doc) != source_tokens:
            raise ValueError(f"{directory}: numeric or URL token mismatch in {locale}")
        used_fn = {node["id"] for block in doc["blocks"] for node in _walk_inline(block) if node.get("t") == "fn"}
        if used_fn != fn_ids:
            raise ValueError(f"{directory}: footnote reference/body mismatch in {locale}")
        used_sources = {node["key"] for block in doc["blocks"] for node in _walk_inline(block) if node.get("t") == "cite"}
        if not used_sources.issubset(set(source_keys)):
            raise ValueError(f"{directory}: citation references a missing source in {locale}")
        used_figs = {block.get("attrs", {}).get("fig") for block in doc["blocks"] if block["type"] == "figure"}
        for fig_id in used_figs:
            fig = figures.get(fig_id)
            if not fig or not fig.get("credit") or not fig.get("licence"):
                raise ValueError(f"{directory}: figure {fig_id} is missing credit or licence")
            for required_locale in LOCALES:
                if piece["locales"][required_locale] == "ready" and (not fig.get("alt", {}).get(required_locale) or not fig.get("caption", {}).get(required_locale)):
                    raise ValueError(f"{directory}: figure {fig_id} is missing alt text or caption in {required_locale}")
    piece["docs"], piece["sources"], piece["figures"] = docs, sources, figures
    piece["provenance"] = provenance
    piece["directory"] = directory
    return piece


def _walk_inline(block: dict):
    def walk(nodes):
        for node in nodes:
            yield node
            if node.get("t") in {"link", "lang"}:
                yield from walk(node.get("c", []))
    yield from walk(block.get("content", []))
    for item in block.get("items", []):
        yield from walk(item)


def _structure(doc: dict) -> tuple:
    citations, figures = [], []
    for block in doc.get("blocks", []):
        if block.get("type") == "figure": figures.append(block.get("attrs", {}).get("fig"))
        for node in _walk_inline(block):
            if node.get("t") == "cite": citations.append(node.get("key"))
    return tuple(sorted(citations)), tuple(figures)


def _tokens(doc: dict) -> tuple:
    numeric, urls = [], []
    url_re = re.compile(r"https?://[^\s<>]+", re.I)
    num_re = re.compile(r"\d+(?:[.,]\d+)*")
    for block in doc.get("blocks", []):
        for node in _walk_inline(block):
            if node.get("t") == "text":
                numeric.extend(num_re.findall(node.get("v", "")))
                urls.extend(url_re.findall(node.get("v", "")))
            elif node.get("t") == "link":
                urls.append(node.get("href", ""))
            elif node.get("t") == "cite":
                numeric.extend(num_re.findall(node.get("locator", "")))
    for value in doc.get("footnotes", {}).values():
        for node in _walk_inline({"content": value}):
            if node.get("t") == "text":
                numeric.extend(num_re.findall(node.get("v", "")))
                urls.extend(url_re.findall(node.get("v", "")))
    return tuple(numeric), tuple(urls)


def load_editorial(root: Path) -> tuple[list[dict], list[dict]]:
    root = Path(root)
    pieces = []
    pieces_root = root / "pieces"
    if pieces_root.exists():
        for directory in sorted(path for path in pieces_root.iterdir() if path.is_dir()):
            pieces.append(load_piece(directory))
    issues = []
    issues_root = root / "issues"
    if issues_root.exists():
        for path in sorted(issues_root.glob("*.json")):
            issue = _load(path)
            _validate(path, "issue.v1.schema.json", issue)
            issues.append(issue)
    return pieces, issues


def write_public_source(root: Path, out: Path, pieces: list[dict], issues: list[dict]) -> None:
    """Copy only validated publication records and referenced figure files."""
    dest = out / "editorial"
    dest.mkdir(parents=True, exist_ok=True)
    for piece in pieces:
        source = piece["directory"]
        target = dest / "pieces" / piece["slug"]
        target.mkdir(parents=True, exist_ok=True)
        for name in ("piece.json", "sources.json", "figures.json", "provenance.json", *(f"doc.{locale}.json" for locale in piece["docs"])):
            shutil.copyfile(source / name, target / name)
        for fig in piece["figures"].values():
            relative = Path(fig["file"])
            target_file = target / relative
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / relative, target_file)
    issue_root = dest / "issues"
    issue_root.mkdir(parents=True, exist_ok=True)
    for issue in issues:
        source = root / "issues" / f"{issue['id']}.json"
        shutil.copyfile(source, issue_root / source.name)


def _essay_body(piece: dict, locale: str, *, base: str) -> tuple[str, str, str, str]:
    words = LOCALE_WORDS[locale]
    piece_id = piece["id"]
    if piece["status"] == "withdrawn":
        note = piece["withdrawal"]["note"].get(locale, "")
        body = (f'<article class="essay essay-withdrawn" data-piece-id="{piece_id}" lang="{locale}">'
                f'<header class="essay-head"><p class="essay-state">{words["withdrawn"]}</p><h1 class="essay-title">{_esc(piece.get("last_titles", {}).get(locale, _title_or_slug(piece, locale)))}</h1>'
                f'<time datetime="{_esc(piece["withdrawal"]["at"])}">{_esc(piece["withdrawal"]["at"][:10])}</time></header>'
                f'<aside class="correction-box"><h2>{words["withdrawal_note"]}</h2><p>{_esc(note)}</p></aside></article>')
        return body, "", "", ""
    if piece["locales"][locale] == "pending" or locale not in piece["docs"]:
        source_loc = piece["source_locale"]
        origin = href(base, piece_path({"path_prefix": PREFIXES[source_loc]}, piece))
        body = (f'<article class="essay essay-pending" data-piece-id="{piece_id}" lang="{locale}">'
                f'<header class="essay-head"><h1 class="essay-title">{_esc(_title_or_slug(piece, locale))}</h1></header>'
                f'<p>{words["pending"]}</p><a href="{_esc(origin)}">{_origin_label(locale)}</a></article>')
        return body, "", "", ""
    doc = piece["docs"][locale]
    content, notes, sources, toc = essay_doc.render_document(doc, piece["sources"], piece["figures"], locale=locale, base=base,
                                                            asset_prefix=f"editorial/pieces/{piece['slug']}")
    author_names = ", ".join(author["name"] for author in piece["authors"])
    byline = f'<p class="essay-byline">{words["by"]} {_esc(author_names)}</p>'
    dt = piece["first_published_at"]
    header = (f'<header class="essay-head"><h1 class="essay-title">{_esc(doc["title"])}</h1>'
              f'<p class="essay-dek">{_esc(doc["dek"])}</p>{byline}<time datetime="{_esc(dt)}">{dt[:10]}</time></header>')
    body = f'<article class="essay" data-piece-id="{piece_id}" lang="{locale}">{header}{toc}<div class="essay-body">{content}</div>{notes}{sources}</article>'
    return body, doc["title"], doc["dek"], ""


def _esc(value: Any) -> str:
    from html import escape
    return escape(str(value), quote=True)


def _title_or_slug(piece: dict, locale: str) -> str:
    doc = piece["docs"].get(locale)
    return doc["title"] if doc else piece["slug"].replace("-", " ").title()


def _origin_label(locale: str) -> str:
    return {"en": "Read the original", "es-419": "Leer el original", "zh-Hans": "阅读原文"}[locale]


def render_piece(piece: dict, locale: str, *, base: str, locale_info: dict | None = None,
                 locales: list[dict] | None = None, catalog: dict | None = None) -> tuple[str, str, str]:
    if piece["status"] != "published" or piece["locales"][locale] != "ready" or locale not in piece["docs"]:
        body, title, dek, _ = _essay_body(piece, locale, base=base)
        return title or _title_or_slug(piece, locale), dek or LOCALE_WORDS[locale]["pending"], body
    doc = piece["docs"][locale]
    title, description = doc["title"], doc["dek"]
    body_html, notes_html, sources_html, toc_html = essay_doc.render_document(
        doc, piece["sources"], piece["figures"], locale=locale, base=base,
        asset_prefix=f"editorial/pieces/{piece['slug']}")
    disclosure = ""
    provenance = piece["provenance"].get(locale, {})
    if provenance.get("human_reviewed") is not True and provenance.get("origin", "").startswith("agent_"):
        original = href(base, piece_path({"path_prefix": PREFIXES[piece["source_locale"]]}, piece))
        disclosure = (f'<aside class="mt-disclosure"><p>{_esc(MACHINE_DISCLOSURE[locale])}</p>'
                      f'<a href="{_esc(original)}">{_origin_label(locale)}</a></aside>')
    body_html = disclosure + toc_html + f'<div class="essay-body">{body_html}</div>'
    template_name = f"{__package__}.templates.essay"
    essay_template = (importlib.import_module(template_name)
                      if importlib.util.find_spec(template_name) is not None else None)
    if essay_template is not None:
        locale_info = locale_info or {"code": locale, "html_lang": locale}
        locale_rows = locales or [{"code": value, "path_prefix": PREFIXES[value], "html_lang": value} for value in LOCALES]
        ctx = {
            "original": href(base, piece_path({"path_prefix": PREFIXES[piece["source_locale"]]}, piece)),
            "other_languages": {row["code"]: href(base, piece_path(row, piece)) for row in locale_rows},
            "shelf": href(base, PREFIXES[locale] + "cartas/"),
            "catalog": catalog or {},
            "base": base,
            "hrefs": {
                "original": href(base, piece_path({"path_prefix": PREFIXES[piece["source_locale"]]}, piece)),
                "shelf": href(base, PREFIXES[locale] + "cartas/"),
                "others": [{"code": row["code"], "label": {"en": "English", "es-419": "Español", "zh-Hans": "简体中文"}[row["code"]],
                            "href": href(base, piece_path(row, piece))} for row in locale_rows if row["code"] != locale],
            },
            "title": title,
            "dek": description,
        }
        return essay_template.render(piece, locale_info, body_html, notes_html, sources_html, ctx)
    author_names = ", ".join(author["name"] for author in piece["authors"])
    header = (f'<header class="essay-head"><h1 class="essay-title">{_esc(title)}</h1>'
              f'<p class="essay-dek">{_esc(description)}</p><p class="essay-byline">{LOCALE_WORDS[locale]["by"]} {_esc(author_names)}</p>'
              f'<time datetime="{_esc(piece["first_published_at"])}">{_esc(piece["first_published_at"][:10])}</time></header>')
    return title, description, f'<article class="essay" data-piece-id="{piece["id"]}" lang="{locale}">{header}{body_html}{notes_html}{sources_html}</article>'


def render_issue(issue: dict, locale: str, pieces_by_id: dict[str, dict], stories_by_id: dict[str, dict], *, base: str, catalog: dict) -> tuple[str, str, str]:
    title = issue["title"][locale]
    e = _esc
    cards = []
    for row in issue["slots"]:
        target = pieces_by_id.get(row["ref"])
        if target:
            label = target["docs"].get(locale, {}).get("title", target["slug"])
            url = href(base, PREFIXES[locale] + "cartas/" + target["slug"] + "/")
        else:
            story = stories_by_id.get(row["ref"])
            if not story:
                raise ValueError(f"issue {issue['id']} references unknown item {row['ref']}")
            from .i18n import headline
            label = headline(story, locale, catalog)
            url = href(base, PREFIXES[locale] + story["url_date"].replace("-", "/") + "/" + story["slug"] + "/")
        cards.append(f'<li data-slot="{e(row["slot"])}"><a href="{e(url)}">{e(label)}</a></li>')
    body = f'<article class="curated-issue" data-issue-id="{e(issue["id"])}"><header><h1>{e(title)}</h1><time datetime="{e(issue["date"])}">{e(issue["date"])}</time></header><p>{e(issue["note"][locale])}</p><ol>{"".join(cards)}</ol></article>'
    return title, issue["note"][locale], body


def piece_search_rows(pieces: list[dict], locale: str, *, base: str) -> list[dict]:
    rows = []
    for piece in pieces:
        if piece["status"] != "published" or piece["locales"][locale] != "ready" or locale not in piece["docs"]:
            continue
        doc = piece["docs"][locale]
        text = " ".join([doc["title"], doc["dek"], *(essay_doc.text_of(b.get("content", [])) for b in doc["blocks"])])
        rows.append({"h": doc["title"], "d": doc["dek"], "u": href(base, piece_path({"path_prefix": PREFIXES[locale]}, piece)), "b": "fCMO", "o": [], "t": piece["tags"], "kind": "essay", "search_text": text})
    return rows


def feed_items(pieces: list[dict], locale: str, *, base_url: str) -> list[dict]:
    rows = []
    for piece in pieces:
        if piece["status"] != "published" or piece["locales"][locale] != "ready" or locale not in piece["docs"]:
            continue
        doc = piece["docs"][locale]
        rows.append({"id": piece["id"], "title": doc["title"], "dek": doc["dek"], "url": absolute(base_url, piece_path({"path_prefix": PREFIXES[locale]}, piece)), "published": piece["first_published_at"], "updated": piece["updated_at"]})
    return rows


def render_shelf(pieces: list[dict], locale: str, *, base: str) -> str:
    rows = []
    for piece in sorted(pieces, key=lambda p: p["first_published_at"], reverse=True):
        if piece["kind"] not in {"letter", "essay", "note"} or piece["status"] != "published":
            continue
        doc = piece["docs"].get(locale)
        if piece["locales"][locale] == "ready" and doc:
            title, dek = doc["title"], doc["dek"]
            url = href(base, piece_path({"path_prefix": PREFIXES[locale]}, piece))
            date = piece["first_published_at"][:10]
            rows.append(f'<article class="story-card"><span class="card-meta">{_esc(date)}</span><h3><a href="{_esc(url)}">{_esc(title)}</a></h3><p>{_esc(dek)}</p></article>')
    if not rows: return ""
    return '<div class="card-row editorial-letters">' + "".join(rows[:12]) + '</div>'


def render_issue_shelf(issues: list[dict], locale: str, *, base: str) -> str:
    if not issues: return ""
    rows = []
    for issue in sorted(issues, key=lambda item: item["date"], reverse=True):
        url = href(base, issue_path({"path_prefix": PREFIXES[locale]}, issue))
        rows.append(f'<article class="story-card"><span class="card-meta">{_esc(issue["date"])}</span><h3><a href="{_esc(url)}">{_esc(issue["title"][locale])}</a></h3><p>{_esc(issue["note"][locale])}</p></article>')
    return '<div class="card-row curated-issues">' + "".join(rows) + '</div>'


def write_feeds(pieces: list[dict], *, locales: list[dict], base_url: str, out: Path) -> None:
    from html import escape
    from email.utils import format_datetime
    from datetime import datetime, timezone
    for locale in locales:
        code = locale["code"]
        rows = feed_items(pieces, code, base_url=base_url)
        if not rows: continue
        feed_rel = locale["path_prefix"] + "feed.xml"
        feed_url = absolute(base_url, feed_rel)
        items = []
        for row in rows:
            date = datetime.fromisoformat(row["published"].replace("Z", "+00:00")).astimezone(timezone.utc)
            items.append(f'<item><title>{escape(row["title"])}</title><link>{escape(row["url"])}</link><guid isPermaLink="false">{escape(row["id"])}</guid><pubDate>{format_datetime(date, usegmt=True)}</pubDate><description>{escape(row["dek"])}</description></item>')
        path = out / feed_rel
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        marker = "</channel></rss>"
        if marker in text:
            text = text.replace(marker, "".join(items) + marker, 1)
        else:
            text = f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>fCMO · {code}</title><link>{escape(absolute(base_url, locale["path_prefix"]))}</link><description>Essays and letters</description><language>{escape(locale["html_lang"])}</language>{"".join(items)}</channel></rss>'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        atom_path = out / locale["path_prefix"] / "feed.atom"
        if atom_path.is_file():
            atom_text = atom_path.read_text(encoding="utf-8")
            entries = []
            for row in rows:
                entries.append(f'<entry><title>{escape(row["title"])}</title><id>{escape(row["url"])}</id><link href="{escape(row["url"])}"/><published>{escape(row["published"])}</published><updated>{escape(row["updated"])}</updated><summary>{escape(row["dek"])}</summary></entry>')
            atom_text = atom_text.replace("</feed>", "".join(entries) + "</feed>", 1)
            atom_path.write_text(atom_text, encoding="utf-8")
        json_path = out / locale["path_prefix"] / "feed.json"
        if json_path.is_file():
            value = json.loads(json_path.read_text(encoding="utf-8"))
            value["items"].extend({"id": row["id"], "url": row["url"], "title": row["title"], "summary": row["dek"], "date_published": row["published"], "date_modified": row["updated"]} for row in rows)
            json_path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
