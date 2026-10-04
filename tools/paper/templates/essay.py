"""Frame for essays, letters and notes (Studio lane B).

The body, notes and sources arrive as HTML from the closed-schema renderer
(`tools/paper/essay_doc.py`, lane A1) using the class contract in STUDIO-SPEC 6.1.
This module only wraps them: header, byline, table of contents, correction box,
machine-preparation notice, pending and withdrawn pages. Every dynamic string
crosses `html.escape`; the A1 fragments are already escaped markup.

ctx keys (all optional except hrefs when links are wanted):
  title, dek, date_text, base, hrefs{original, shelf, others[{code,label,href}]},
  mode ("essay" | "pending" | "tombstone"), machine_prepared (bool),
  assets (URL prefix of the site assets, default base + "assets/"),
  catalog (unused today, reserved for shared strings).
"""

from __future__ import annotations

from html import escape
import math
import re

COPY = {
    "en": {
        "kind": {"essay": "Essay", "letter": "Letter", "note": "Note"}, "by": "By", "min": "min read",
        "toc": "In this piece", "notes": "Notes", "sources": "Sources", "original": "Read the original",
        "mt_title": "Prepared with machine translation",
        "mt_body": "This language version was prepared by a machine and has not been reviewed by a person. The original text is the reference.",
        "correction": "Correction", "clarification": "Clarification", "substantive": "Substantive correction",
        "pending": "This text is not available in English yet.", "pending_body": "The original is available now.",
        "withdrawn": "This text was withdrawn", "withdrawn_on": "Withdrawn on", "back": "All letters",
        "languages": "Read in", "note_label": "Note", "updated": "Updated",
    },
    "es-419": {
        "kind": {"essay": "Ensayo", "letter": "Carta", "note": "Nota"}, "by": "Por", "min": "min de lectura",
        "toc": "En este texto", "notes": "Notas", "sources": "Fuentes", "original": "Leer el original",
        "mt_title": "Preparado con traducción automática",
        "mt_body": "Esta versión fue preparada por una máquina y todavía no la ha revisado una persona. El texto original es la referencia.",
        "correction": "Corrección", "clarification": "Aclaración", "substantive": "Corrección de fondo",
        "pending": "Este texto todavía no está disponible en español.", "pending_body": "El original ya puede leerse.",
        "withdrawn": "Este texto fue retirado", "withdrawn_on": "Retirado el", "back": "Todas las cartas",
        "languages": "Leer en", "note_label": "Nota", "updated": "Actualizado",
    },
    "zh-Hans": {
        "kind": {"essay": "随笔", "letter": "来信", "note": "短札"}, "by": "作者", "min": "分钟",
        "toc": "本文目录", "notes": "注释", "sources": "来源", "original": "阅读原文",
        "mt_title": "机器翻译版本",
        "mt_body": "此语言版本由机器准备，尚未经人工审阅。请以原文为准。",
        "correction": "更正", "clarification": "说明", "substantive": "实质更正",
        "pending": "本文暂无中文版本。", "pending_body": "可以先阅读原文。",
        "withdrawn": "本文已撤回", "withdrawn_on": "撤回日期", "back": "全部来信",
        "languages": "其他语言", "note_label": "注", "updated": "更新",
    },
}

_TAG = re.compile(r"<[^>]+>")
_CJK = re.compile(r"[㐀-鿿豈-﫿]")
_HEADING = re.compile(r'<(h[23])\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</\1>', re.S)

SIDENOTES = r"""<script>(()=>{const a=document.querySelector('article.essay');if(!a)return;const wide=matchMedia('(min-width:1100px)');const body=a.querySelector('.essay-body');const notes=a.querySelector('.essay-notes');if(!body||!notes)return;
const refs=[...body.querySelectorAll('sup.fn-ref a')];let side=[];
function clear(){side.forEach(n=>n.remove());side=[];a.classList.remove('has-sidenotes');body.querySelectorAll('.fn-inline').forEach(n=>n.remove())}
function lay(){clear();if(!wide.matches)return;const top0=body.getBoundingClientRect().top+scrollY;let floor=0;
refs.forEach((r,i)=>{const li=notes.querySelector((r.getAttribute('href')||'').replace(/^#/,'#'));if(!li)return;const n=document.createElement('aside');n.className='sidenote';n.setAttribute('role','note');
const c=li.cloneNode(true);c.querySelectorAll('a[href^="#fnref"]').forEach(x=>x.remove());n.innerHTML='<span class="sidenote-n">'+(i+1)+'</span> '+c.innerHTML;body.appendChild(n);
const y=Math.max(r.getBoundingClientRect().top+scrollY-top0-4,floor);n.style.top=y+'px';floor=y+n.offsetHeight+12;side.push(n)});if(side.length)a.classList.add('has-sidenotes')}
body.addEventListener('click',e=>{const r=e.target.closest('sup.fn-ref a');if(!r||wide.matches)return;e.preventDefault();const li=notes.querySelector(r.getAttribute('href'));if(!li)return;const p=r.closest('p,li,blockquote')||r.parentElement;const open=p.nextElementSibling;
if(open&&open.classList.contains('fn-inline')&&open.dataset.for===r.id){open.remove();r.setAttribute('aria-expanded','false');return}
body.querySelectorAll('.fn-inline').forEach(n=>n.remove());const s=document.createElement('p');s.className='fn-inline';s.dataset.for=r.id;const c=li.cloneNode(true);c.querySelectorAll('a[href^="#fnref"]').forEach(x=>x.remove());s.innerHTML=c.innerHTML;p.after(s);r.setAttribute('aria-expanded','true')});
wide.addEventListener('change',lay);addEventListener('load',lay);document.fonts&&document.fonts.ready.then(lay);lay()})()</script>"""


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _text(html: str) -> str:
    return _TAG.sub(" ", html)


def reading_minutes(body_html: str) -> int:
    text = _text(body_html)
    cjk = len(_CJK.findall(text))
    words = len(_CJK.sub(" ", text).split())
    return max(1, math.ceil(cjk / 400 + words / 230)) if (cjk or words) else 1


def _date(value: str | None) -> str:
    return (value or "")[:10]


def _toc(body_html: str, c: dict) -> str:
    items = _HEADING.findall(body_html)
    if len(items) < 2:
        return ""
    rows, open_sub = [], False
    for tag, ident, inner in items:
        label = _e(re.sub(r"\s+", " ", _text(inner)).strip())
        if tag == "h2":
            rows.append(("</ol></li>" if open_sub else ("</li>" if rows else "")) + f'<li><a href="#{_e(ident)}">{label}</a>')
            open_sub = False
        else:
            rows.append(("" if open_sub else "<ol>") + f'<li><a href="#{_e(ident)}">{label}</a></li>')
            open_sub = True
    tail = "</ol></li>" if open_sub else "</li>"
    return f'<nav class="essay-toc" aria-label="{_e(c["toc"])}"><p class="essay-toc-title">{_e(c["toc"])}</p><ol>' + "".join(rows) + tail + "</ol></nav>"


def _authors(piece: dict) -> str:
    return " · ".join(_e(a.get("name", "")) for a in piece.get("authors", []) if a.get("name"))


def _kicker(piece: dict, c: dict) -> str:
    keys = {a.get("key") for a in piece.get("authors", [])}
    brand = "fCMO / Javier" if keys == {"javier"} else "FCMO AI / Matías" if keys == {"matias"} else "FCMO"
    return f'<p class="essay-kicker">{_e(brand)} · {_e(c["kind"].get(piece.get("kind", "essay"), c["kind"]["essay"]))}</p>'


def _languages(hrefs: dict, c: dict) -> str:
    others = hrefs.get("others") or []
    if not others:
        return ""
    links = "".join(f'<a href="{_e(o["href"])}" hreflang="{_e(o["code"])}" lang="{_e(o["code"])}">{_e(o["label"])}</a>' for o in others)
    return f'<nav class="essay-langs" aria-label="{_e(c["languages"])}"><span>{_e(c["languages"])}</span>{links}</nav>'


def _corrections(piece: dict, loc: str, c: dict) -> str:
    out = []
    for item in piece.get("corrections", []):
        note = (item.get("note") or {}).get(loc)
        if not note:
            continue
        label = c["substantive"] if item.get("type") == "substantive" else c["clarification"]
        out.append(f'<aside class="correction-box"><p><strong>{_e(label)}</strong> · <time datetime="{_e(_date(item.get("at")))}">{_e(_date(item.get("at")))}</time></p><p>{_e(note)}</p></aside>')
    return "".join(out)


def render(piece: dict, locale: dict, body_html: str, notes_html: str, sources_html: str, ctx: dict) -> tuple[str, str, str]:
    loc = locale["code"]
    c = COPY[loc]
    hrefs = ctx.get("hrefs") or {}
    base = ctx.get("base", "/")
    assets = ctx.get("assets") or (base.rstrip("/") + "/assets/")
    title = ctx.get("title") or piece.get("slug", "")
    dek = ctx.get("dek") or ""
    mode = ctx.get("mode", "essay")
    css = f'<link rel="stylesheet" href="{_e(assets)}css/essay.css">'
    attrs = f'class="essay" data-piece-id="{_e(piece.get("id", ""))}" data-kind="{_e(piece.get("kind", "essay"))}" lang="{_e(locale["html_lang"])}"'
    original = hrefs.get("original")
    head_core = f'{_kicker(piece, c)}<h1 class="essay-title">{_e(title)}</h1>' + (f'<p class="essay-dek">{_e(dek)}</p>' if dek else "")
    shelf = f'<p class="essay-back"><a href="{_e(hrefs["shelf"])}">← {_e(c["back"])}</a></p>' if hrefs.get("shelf") else ""

    if mode == "pending":
        orig = f'<p><a class="essay-original" href="{_e(original)}">{_e(c["original"])} →</a></p>' if original else ""
        body = (f'{css}<article {attrs} data-state="pending"><header class="essay-head">{head_core}</header>'
                f'<div class="essay-state"><p class="essay-state-line">{_e(c["pending"])}</p><p>{_e(c["pending_body"])}</p>{orig}</div>{_languages(hrefs, c)}{shelf}</article>')
        return f'{title} — FCMO', c["pending"], body
    if mode == "tombstone":
        w = piece.get("withdrawal") or {}
        note = (w.get("note") or {}).get(loc, "")
        body = (f'{css}<article {attrs} data-state="withdrawn"><header class="essay-head">{head_core}</header>'
                f'<div class="essay-state"><p class="essay-state-line">{_e(c["withdrawn"])}</p>'
                f'<p>{_e(c["withdrawn_on"])} <time datetime="{_e(_date(w.get("at")))}">{_e(ctx.get("withdrawn_text") or _date(w.get("at")))}</time>.</p>'
                + (f'<p>{_e(note)}</p>' if note else "") + f'</div>{shelf}</article>')
        return f'{title} — FCMO', c["withdrawn"], body

    published = _date(piece.get("first_published_at"))
    date_text = ctx.get("date_text") or published
    minutes = reading_minutes(body_html)
    byline = (f'<p class="essay-byline"><span class="essay-by">{_e(c["by"])} {_authors(piece)}</span>'
              f'<time datetime="{_e(published)}">{_e(date_text)}</time><span class="essay-read">{minutes} {_e(c["min"])}</span></p>')
    disclosure = ""
    if ctx.get("machine_prepared"):
        orig = f' <a href="{_e(original)}">{_e(c["original"])} →</a>' if original else ""
        disclosure = f'<aside class="mt-disclosure" role="note"><p><strong>{_e(c["mt_title"])}</strong></p><p>{_e(c["mt_body"])}{orig}</p></aside>'
    header = body_html.lstrip().startswith('<header class="essay-head"')
    head_html = "" if header else f'<header class="essay-head">{head_core}{byline}</header>'
    description = dek or re.sub(r"\s+", " ", _text(body_html)).strip()[:160]
    body = (f'{css}<article {attrs}>{head_html}{disclosure}{_toc(body_html, c)}'
            f'<div class="essay-body">{body_html}</div>{notes_html}{sources_html}{_corrections(piece, loc, c)}'
            f'{_languages(hrefs, c)}{shelf}</article>{SIDENOTES}')
    return f'{title} — FCMO', description, body
