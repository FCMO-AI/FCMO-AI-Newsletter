"""Shared page chrome. All dynamic text crosses html.escape here or upstream."""

from __future__ import annotations

from html import escape
import json
from tools.paper.routes import PRODUCT_NAMES, TECHNICAL_FRONT


MASTHEAD_SUBTITLE = {
    "en": "Newsletter · evidence first",
    "es-419": "Newsletter · evidencia primero",
    "zh-Hans": "简报 · 证据优先",
}


def _e(value: object, *, quote: bool = True) -> str:
    return escape(str(value), quote=quote)


def _url(base: str, path: str = "") -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def document(*, locale: dict, catalog: dict, config: dict, base: str, path: str,
             title: str, description: str, body: str, canonical: str,
             alternates: list[tuple[str, str]], og_image: str | None = None,
             page_type: str = "website", status_banner: str = "",
             json_ld: dict | None = None, extra_head: str = "",
             body_class: str = "", story_id: str | None = None) -> str:
    strings = catalog["strings"]
    lang = locale["html_lang"]
    locale_prefix = locale["path_prefix"]
    home = _url(base, locale_prefix)
    css = _url(base, "assets/css/paper.css")
    favicon = _url(base, "assets/pwa/favicon.svg")
    apple_touch_icon = _url(base, "assets/pwa/icons/icon-192.svg")
    font_root = _url(base, "assets/fonts/")
    search = _url(base, locale_prefix + "search/")
    archive = _url(base, locale_prefix + "archive/")
    feeds = _url(base, locale_prefix + "feeds/")
    status = _url(base, locale_prefix + "status/")
    method = _url(base, locale_prefix + "method/")
    technical = _url(base, locale_prefix + TECHNICAL_FRONT)
    is_technical = path.startswith(TECHNICAL_FRONT) or body_class not in {"page-landing", "page-subscribe"}
    alternates_html = "\n".join(
        f'<link rel="alternate" hreflang="{_e(code)}" href="{_e(url)}">'
        for code, url in alternates
    )
    languages = "".join(
        f'<a href="{_e(url)}" hreflang="{_e(code)}" lang="{_e(code)}"'
        + (' aria-current="page"' if code == locale["hreflang"] else "")
        + f'>{_e(label)}</a>'
        for code, url, label in (
            (item["hreflang"], _url(base, item["path_prefix"] + path), item["label"])
            for item in config["locales"]
        )
    )
    crumb_label = {"en": "Home", "es-419": "Inicio", "zh-Hans": "首页"}[locale["code"]]
    current_crumb = ({"en": "Organization", "es-419": "Organización", "zh-Hans": "机构"}[locale["code"]]
                     if path.startswith("org/") else title.split(" — ")[0])
    breadcrumb = "" if not path else (f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol><li><a href="{_e(home)}">{_e(crumb_label)}</a></li>'
        + (f'<li><a href="{_e(technical)}">{_e(PRODUCT_NAMES["technical"])}</a></li>' if is_technical and path != TECHNICAL_FRONT else "")
        + f'<li aria-current="page">{_e(current_crumb)}</li></ol></nav>')
    nav = strings["nav"]
    footer = strings["footer"]
    year = canonical[0:4] if canonical[:4].isdigit() else "2026"
    og = f'<meta property="og:image" content="{_e(og_image)}"><meta name="twitter:card" content="summary_large_image">' if og_image else ""
    structured = ""
    if json_ld:
        structured = '<script type="application/ld+json">' + json.dumps(json_ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    # A tiny progressive enhancement: stale fallback and legacy fragment mapping.
    safeguard = r"""<script>(()=>{let b=document.querySelector('[data-edition-at]');if(b&&Date.now()-Date.parse(b.dataset.editionAt)>1296e5){b.hidden=false;b.dataset.editionState='DELAYED'}let m=location.hash.match(/^#\/brief\/(FCMO-[A-F0-9]{12})/);if(m)location.replace(document.documentElement.dataset.storyBase+m[1]+'.html')})()</script>"""
    return f'''<!doctype html>
<html lang="{_e(lang)}" data-story-base="{_e(_url(base, locale_prefix + 'legacy-story/'))}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title><meta name="description" content="{_e(description[:160])}">
<link rel="icon" href="{_e(favicon)}" type="image/svg+xml"><link rel="apple-touch-icon" href="{_e(apple_touch_icon)}">
<link rel="canonical" href="{_e(canonical)}">{alternates_html}
<link rel="preload" href="{_e(font_root + 'InterTight-normal-400_900-latin.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{_e(font_root + 'SourceSerif4-normal-400_700-latin.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{_e(font_root + 'JetBrainsMono-normal-400-latin.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{_e(css)}"><meta name="theme-color" content="#F2EFE8">
<meta property="og:type" content="{_e(page_type)}"><meta property="og:title" content="{_e(title)}"><meta property="og:description" content="{_e(description[:160])}"><meta property="og:url" content="{_e(canonical)}">{og}
{structured}{extra_head}
<!-- agent-alternates -->
</head>
<body class="{_e(body_class)}"><a class="skip-link" href="#main">{_e(strings['a11y']['skip_to_content'])}</a>
<header class="site-header"><div class="utility-bar"><a class="utility-brand" href="{_e(home)}">FCMO <span>GROUP</span></a><span class="edition-line">{_e(strings['site']['tagline'])}</span><nav class="language-nav" aria-label="{_e(strings['a11y']['language_switcher'])}">{languages}</nav></div>
<div class="masthead"><a class="brand" href="{_e(home)}">FCMO</a><span class="brand-sub">{_e(PRODUCT_NAMES['newsletter'])} · FCMO Group</span></div>
<nav class="zone-switch" aria-label="Publication sections"><a href="{_e(home)}"{' aria-current="page"' if not is_technical else ''}>{_e(PRODUCT_NAMES['newsletter'])}<small>FCMO Group</small></a><a href="{_e(technical)}"{' aria-current="page"' if is_technical else ''}>{_e(PRODUCT_NAMES['technical'])}<small>FCMO AI</small></a></nav>
<nav class="main-nav" aria-label="{_e(nav['menu'])}"><a href="{_e(home)}">{_e(nav['home'])}</a><a href="{_e(technical)}">{_e(PRODUCT_NAMES['technical'])}</a><a href="{_e(archive)}">{_e(nav['archive'])}</a><a href="{_e(search)}">{_e(nav['search'])}</a><a href="{_e(feeds)}">{_e(nav['feeds'])}</a><a href="{_e(method)}">{_e(nav['method'])}</a><a href="{_e(status)}">{_e(nav['status'])}</a></nav></header>
{status_banner}<main id="main" class="page-shell"{f' data-story-id="{_e(story_id)}"' if story_id else ''}>{breadcrumb}{body}</main>
<footer class="site-footer"><div class="footer-inner"><div class="footer-brand"><a href="{_e(home)}">FCMO <span>GROUP</span></a><a href="{_e(technical)}">FCMO AI</a></div><nav class="footer-links" aria-label="Footer"><a href="{_e(_url(base, locale_prefix+'about/'))}">{_e(footer['about'])}</a><a href="{_e(method)}">{_e(footer['method'])}</a><a href="{_e(_url(base, locale_prefix+'corrections/'))}">{_e(footer['corrections'])}</a><a href="{_e(_url(base, locale_prefix+'privacy/'))}">{_e(footer['privacy'])}</a><a href="{_e(_url(base, locale_prefix+'license/'))}">{_e(footer['license'])}</a><a href="{_e(_url(base, locale_prefix+'disclaimer/'))}">{_e(footer['disclaimer'])}</a><a href="{_e(status)}">{_e(footer['status'])}</a><a href="{_e(feeds)}">{_e(footer['feeds'])}</a></nav><p class="footer-note">{_e(footer['automated_notice'])}<br>{_e(footer['copyright'].format(year=year))} · Faber Consilii, Machinator Operis</p></div></footer>{safeguard}</body></html>'''
