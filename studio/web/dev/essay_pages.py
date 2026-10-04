"""Build the sample essay in en, es-419 and zh-Hans through the real page frame.

usage: python3 studio/web/dev/essay_pages.py OUT_DIR
Uses a tiny stand-in for lane A1's renderer (same 6.1 class contract) so the frame
and CSS can be inspected before A1 lands. Not shipped; the production build uses
tools/paper/essay_doc.py.
"""
from __future__ import annotations

import json
from html import escape as e
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.paper import i18n  # noqa: E402
from tools.paper.templates import essay, layout  # noqa: E402


def inline(nodes, fnorder, src):
    out = []
    for n in nodes:
        if n["t"] == "text":
            v = e(n["v"])
            for m in n.get("marks", []):
                v = f"<{'em' if m == 'em' else 'strong'}>{v}</{'em' if m == 'em' else 'strong'}>"
            out.append(v)
        elif n["t"] == "fn":
            fnorder.append(n["id"]); k = len(fnorder)
            out.append(f'<sup class="fn-ref"><a href="#{n["id"]}" id="fnref-{n["id"][3:]}">{k}</a></sup>')
        elif n["t"] == "cite":
            out.append(f'<cite class="src-ref"><a href="#src-{n["key"][4:]}">{e(n["key"][4:].upper())}</a></cite>')
    return "".join(out)


def render_doc(doc, figures, loc, assets):
    fnorder, parts, hn = [], [], 0
    for b in doc["blocks"]:
        ty = b["type"]
        if ty in ("h2", "h3"):
            hn += 1; parts.append(f'<{ty} id="s-{hn}">{inline(b["content"], fnorder, 0)}</{ty}>')
        elif ty == "p":
            parts.append(f'<p>{inline(b["content"], fnorder, 0)}</p>')
        elif ty == "pullquote":
            parts.append(f'<aside class="pullquote"><p>{inline(b["content"], fnorder, 0)}</p></aside>')
        elif ty == "figure":
            f = figures.get(b["attrs"]["fig"], {"file": ""})
            parts.append(f'<figure class="essay-figure"><img src="{assets}{f["file"]}" width="{f.get("width",1200)}" height="{f.get("height",630)}" alt="{e(f.get("alt",{}).get(loc,""))}"><figcaption>{e(f.get("caption",{}).get(loc,""))} <span class="credit">{e(f.get("credit",""))} · {e(f.get("licence",""))}</span></figcaption></figure>')
        elif ty == "evidence":
            a = b["attrs"]
            parts.append(f'<aside class="evidence-box" data-class="{a["class"]}"><p><strong>{e(a["confidence"])}</strong></p><p>{inline(a["limits"], fnorder, 0)}</p></aside>')
    notes = "".join(f'<li id="{i}">{inline(doc["footnotes"][i], [], 0)} <a href="#fnref-{i[3:]}">↩</a></li>' for i in fnorder)
    return "".join(parts), f'<section class="essay-notes"><ol>{notes}</ol></section>'


def preview(req: dict) -> str:
    """One page for the dev mock: req = {piece, doc, sources, figures, locale, theme}."""
    config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
    catalogs = i18n.load_catalogs(ROOT)
    locale = next(l for l in config["locales"] if l["code"] == req["locale"])
    piece, doc, code = req["piece"], req["doc"], req["locale"]
    body, notes = render_doc(doc, req["figures"], code, "/assets/")
    src = "<section class=\"essay-sources\"><ol>" + "".join(f'<li id="src-{s["key"][4:]}">{e(s.get("author",""))}. <i>{e(s.get("title",""))}</i>. {e(s.get("publisher",""))}</li>' for s in req["sources"]) + "</ol></section>" if req["sources"] else ""
    ctx = {"title": doc["title"] or "(sin título)", "dek": doc.get("dek", ""), "base": "/", "date_text": "", "hrefs": {"others": []}, "machine_prepared": bool(req.get("machine"))}
    title, desc, html = essay.render(piece, locale, body, notes, src, ctx)
    page = layout.document(locale=locale, catalog=catalogs[code], config=config, base="/", path="cartas/x/", title=title, description=desc, body=html,
                           canonical="https://example.invalid/", alternates=[], body_class="page-letters")
    if req.get("theme") in ("light", "dark"):
        page = page.replace("<html ", f'<html data-theme="{req["theme"]}" ', 1)
    return page


def main(out: Path) -> None:
    data = json.loads(subprocess.check_output(["node", str(Path(__file__).with_name("fixture.mjs")), "--json"]))
    config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
    catalogs = i18n.load_catalogs(ROOT)
    shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    (out / "assets").mkdir()
    for child in (ROOT / "site-src" / "assets").iterdir():
        (out / "assets" / child.name).symlink_to(child)
    (out / "assets" / "figures").symlink_to(Path(__file__).with_name("figures"))
    piece = data["piece"]
    srcs = data["sources"]
    for locale in config["locales"]:
        code = locale["code"]; doc = data["docs"][code]
        body, notes = render_doc(doc, data["figures"], code, "/assets/")
        sources = "<section class=\"essay-sources\"><ol>" + "".join(f'<li id="src-{s["key"][4:]}">{e(s["author"])}. <i>{e(s["title"])}</i>. {e(s["publisher"])}, {s["date"][:4]}. <a href="{e(s["url"])}">{e(s["url"])}</a></li>' for s in srcs) + "</ol></section>"
        others = [{"code": o["code"], "label": o["label"], "href": "/" + o["path_prefix"] + "cartas/" + piece["slug"] + "/"} for o in config["locales"] if o["code"] != code]
        ctx = {"title": doc["title"], "dek": doc["dek"], "base": "/", "date_text": {"en": "October 4, 2026", "es-419": "4 de octubre de 2026", "zh-Hans": "2026年10月4日"}[code],
               "hrefs": {"original": "/es/cartas/" + piece["slug"] + "/", "shelf": "/" + locale["path_prefix"] + "cartas/", "others": others},
               "machine_prepared": code == "zh-Hans"}
        title, desc, html = essay.render(piece, locale, body, notes, sources, ctx)
        path = locale["path_prefix"] + "cartas/" + piece["slug"] + "/"
        page = layout.document(locale=locale, catalog=catalogs[code], config=config, base="/", path=path, title=title, description=desc, body=html,
                               canonical="https://example.invalid/" + path, alternates=[], body_class="page-letters")
        d = out / path; d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    if sys.argv[1] == "--stdin":
        sys.stdout.write(preview(json.load(sys.stdin)))
    else:
        main(Path(sys.argv[1]))
