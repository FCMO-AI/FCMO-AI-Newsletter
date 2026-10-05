"""Closed essay document renderer shared by static publication and Studio preview."""
from __future__ import annotations

from html import escape
import re
from typing import Any

from tests.harness.validate import Validator


def _schema():
    from pathlib import Path
    return __import__("json").loads((Path(__file__).resolve().parents[2] / "contracts/essay-doc.v1.schema.json").read_text(encoding="utf-8"))


def validate_document(doc: dict) -> list[str]:
    return Validator(_schema()).errors(doc)


def text_of(nodes: list[dict]) -> str:
    parts = []
    for node in nodes:
        if node.get("t") == "text":
            parts.append(node.get("v", ""))
        elif node.get("t") == "link" or node.get("t") == "lang":
            parts.append(text_of(node.get("c", [])))
        elif node.get("t") == "cite":
            parts.append(node.get("locator", ""))
    return "".join(parts)


def _inline(nodes: list[dict], source_keys: set[str], locale: str) -> str:
    out = []
    for node in nodes:
        kind = node["t"]
        if kind == "text":
            value = escape(node["v"], quote=False)
            marks = set(node.get("marks", []))
            if "strong" in marks: value = f"<strong>{value}</strong>"
            if "em" in marks: value = f"<em>{value}</em>"
            out.append(value)
        elif kind == "link":
            href = escape(node["href"], quote=True)
            out.append(f'<a href="{href}">{_inline(node["c"], source_keys, locale)}</a>')
        elif kind == "fn":
            out.append(f'<sup class="fn-ref"><a href="#fn-{node["id"][3:]}" id="fnref-{node["id"][3:]}">{node["id"][3:]}</a></sup>')
        elif kind == "cite":
            key = node["key"]
            if key not in source_keys:
                raise ValueError(f"citation references missing source {key}")
            label = key + (f", {node['locator']}" if node.get("locator") else "")
            out.append(f'<cite class="src-ref"><a href="#src-{escape(key, quote=True)}">{escape(label)}</a></cite>')
        elif kind == "lang":
            lang = escape(node["lang"], quote=True)
            quoted = _inline(node["c"], source_keys, locale)
            out.append(f'<span class="quote-orig" lang="{lang}" translate="no" data-field="quotation">{quoted}</span>')
        else:
            raise ValueError(f"unsupported inline node {kind!r}")
    return "".join(out)


def render_document(doc: dict, sources: list[dict], figures: dict[str, dict], *, locale: str,
                    base: str = "/", asset_prefix: str = "") -> tuple[str, str, str, str]:
    """Return semantic body, notes, sources and TOC HTML. Reject invalid structures."""
    errors = validate_document(doc)
    if errors:
        raise ValueError("invalid essay document: " + "; ".join(errors[:5]))
    source_keys = {source["key"] for source in sources}
    toc = []
    body = []
    for block in doc["blocks"]:
        kind, bid = block["type"], escape(block["id"], quote=True)
        content = block.get("content", [])
        rendered = _inline(content, source_keys, locale)
        if kind in {"p", "h2", "h3"}:
            tag = kind
            if kind in {"h2", "h3"}:
                toc.append(f'<li class="toc-{kind}"><a href="#{bid}">{rendered}</a></li>')
                body.append(f'<{tag} id="{bid}">{rendered}</{tag}>')
            else:
                body.append(f'<p id="{bid}">{rendered}</p>')
        elif kind in {"blockquote", "pullquote"}:
            tag = "blockquote" if kind == "blockquote" else "aside"
            cls = ' class="pullquote"' if kind == "pullquote" else ""
            cite = block.get("attrs", {}).get("cite")
            if cite and cite in source_keys:
                rendered += f'<cite><a href="#src-{escape(cite, quote=True)}">{escape(cite)}</a></cite>'
            body.append(f'<{tag} id="{bid}"{cls}>{rendered}</{tag}>')
        elif kind in {"ul", "ol"}:
            items = "".join(f"<li>{_inline(item, source_keys, locale)}</li>" for item in block["items"])
            body.append(f'<{kind} id="{bid}">{items}</{kind}>')
        elif kind == "hr":
            body.append(f'<hr id="{bid}" aria-hidden="true">')
        elif kind == "figure":
            fig_id = block["attrs"]["fig"]
            fig = figures.get(fig_id)
            if not fig: raise ValueError(f"figure block references missing figure {fig_id}")
            alt = escape(fig.get("alt", {}).get(locale, ""), quote=True)
            caption = escape(fig.get("caption", {}).get(locale, ""), quote=False)
            credit = escape(fig.get("credit", ""), quote=False)
            src = escape(base.rstrip("/") + "/" + asset_prefix.strip("/") + "/" + fig["file"].lstrip("/"), quote=True)
            body.append(f'<figure id="{bid}" class="essay-figure"><img src="{src}" width="{int(fig["width"])}" height="{int(fig["height"])}" alt="{alt}" loading="lazy"><figcaption>{caption} <span class="credit">{credit}</span></figcaption></figure>')
        elif kind == "evidence":
            attrs = block["attrs"]
            limits = _inline(attrs["limits"], source_keys, locale)
            body.append(f'<aside id="{bid}" class="evidence-box" data-class="{escape(attrs["class"], quote=True)}"><p><strong>{escape(attrs["class"])}</strong> · {escape(attrs["confidence"], quote=False)}</p><p>{limits}</p></aside>')
        else:
            raise ValueError(f"unsupported block node {kind!r}")
    notes = []
    for fid, content in doc["footnotes"].items():
        short = fid[3:]
        notes.append(f'<li id="fn-{short}">{_inline(content, source_keys, locale)} <a href="#fnref-{short}" aria-label="Back to note reference">↩</a></li>')
    notes_html = f'<section class="essay-notes"><h2>{_notes_label(locale)}</h2><ol>{"".join(notes)}</ol></section>' if notes else ""
    source_rows = []
    for source in sources:
        key = escape(source["key"], quote=True)
        title = escape(source["title"], quote=False)
        url = escape(source["url"], quote=True)
        author = escape(source.get("author", ""), quote=False)
        source_rows.append(f'<li id="src-{key}"><a href="{url}" rel="noopener noreferrer">{title}</a>{f" · {author}" if author else ""}</li>')
    sources_html = f'<section class="essay-sources"><h2>{_sources_label(locale)}</h2><ol>{"".join(source_rows)}</ol></section>' if source_rows else ""
    toc_html = f'<nav class="essay-toc" aria-label="{_toc_label(locale)}"><ol>{"".join(toc)}</ol></nav>' if toc else ""
    return "".join(body), notes_html, sources_html, toc_html


def _notes_label(locale: str) -> str:
    return {"en": "Notes", "es-419": "Notas", "zh-Hans": "注释"}[locale]


def _sources_label(locale: str) -> str:
    return {"en": "Sources", "es-419": "Fuentes", "zh-Hans": "来源"}[locale]


def _toc_label(locale: str) -> str:
    return {"en": "On this page", "es-419": "En esta página", "zh-Hans": "本页目录"}[locale]
