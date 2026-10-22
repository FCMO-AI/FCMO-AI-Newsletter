"""Shared page chrome. All dynamic text crosses html.escape here or upstream."""

from __future__ import annotations

from html import escape
import json


LANG_BUTTONS = {"en": "EN", "es-419": "ES", "zh-Hans": "中文"}


def _e(value: object, *, quote: bool = True) -> str:
    return escape(str(value), quote=quote)


def _url(base: str, path: str = "") -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def agent_alternates(resources: list[tuple[str, str]] | None) -> str:
    """Render machine-readable representations attached to this page."""
    if not resources:
        return ""
    return "\n".join(
        f'<link rel="alternate" type="{_e(media_type)}" href="{_e(url)}">'
        for media_type, url in resources
    )


def document(*, locale: dict, catalog: dict, config: dict, base: str, path: str,
             title: str, description: str, body: str, canonical: str,
             alternates: list[tuple[str, str]], og_image: str | None = None,
             page_type: str = "website", status_banner: str = "",
             json_ld: dict | None = None, extra_head: str = "",
             body_class: str = "", story_id: str | None = None,
             machine_alternates: list[tuple[str, str]] | None = None) -> str:
    strings = catalog["strings"]
    lang = locale["html_lang"]
    locale_prefix = locale["path_prefix"]
    home = _url(base, locale_prefix)
    css = _url(base, "assets/css/paper.css")
    favicon = _url(base, "assets/pwa/favicon.svg")
    apple_touch_icon = _url(base, "assets/pwa/icons/icon-192.svg")
    font_root = _url(base, "assets/fonts/")
    search = _url(base, locale_prefix + "search/")
    search_focus = search + "?focus=1"
    archive = _url(base, locale_prefix + "archive/")
    feeds = _url(base, locale_prefix + "feeds/")
    status = _url(base, locale_prefix + "status/")
    method = _url(base, locale_prefix + "method/")
    corrections = _url(base, locale_prefix + "corrections/")
    subscribe = _url(base, locale_prefix + "suscribete/")
    topics = home + "#topics"
    brand_sym = _url(base, "assets/pwa/favicon.svg")
    alternates_html = "\n".join(
        f'<link rel="alternate" hreflang="{_e(code)}" href="{_e(url)}">'
        for code, url in alternates
    )
    nav = strings["nav"]
    tabs = strings["tabs"]
    switch = strings["lang_switch"]
    code = locale["code"]
    alt_map = {hl: u for hl, u in alternates}

    def lang_link(item: dict) -> str:
        hl = item["hreflang"]
        url = alt_map.get(hl) or _url(base, item["path_prefix"] + path)
        note = switch["keeps_story"]
        if alt_map and hl not in alt_map:
            url = _url(base, item["path_prefix"])
            note = switch["story_unavailable"].format(language=item["label"])
        current = hl == locale["hreflang"]
        if current:
            note = switch["current"].format(language=item["label"])
        return (f'<a href="{_e(url)}" hreflang="{_e(hl)}" lang="{_e(hl)}" aria-label="{_e(item["label"])}" title="{_e(note)}"'
                + (' aria-current="true"' if current else "")
                + f'>{_e(LANG_BUTTONS.get(item["code"], item["code"]))}</a>')

    languages = "".join(lang_link(item) for item in config["locales"])
    crumb_label = nav["home"]
    current_crumb = ({"en": "Organization", "es-419": "Organización", "zh-Hans": "机构"}[code]
                     if path.startswith("org/") else title.split(" — ")[0])
    breadcrumb = "" if not path else (
        f'<nav class="breadcrumbs" aria-label="{_e(strings["a11y"]["breadcrumbs"])}"><ol>'
        f'<li><a href="{_e(home)}">{_e(crumb_label)}</a></li><li aria-current="page">{_e(current_crumb)}</li></ol></nav>')

    def here(*prefixes: str) -> str:
        return ' aria-current="page"' if any(path.startswith(p) if p else not path for p in prefixes) else ""

    top_items = (
        (home, nav["today"], here("")),
        (topics, nav["topics"], ""),
        (archive, nav["archive"], here("archive/")),
        (search_focus, nav["search"], here("search/")),
        (corrections, nav["corrections"], here("corrections/")),
        (method, nav["method_short"], here("method/")),
    )
    topnav = "".join(f'<a href="{_e(u)}"{c}>{_e(t)}</a>' for u, t, c in top_items)
    tab_items = (
        (home, tabs["today"], here("")),
        (archive, tabs["archive"], here("archive/")),
        (search_focus, tabs["search"], here("search/")),
        (corrections, tabs["corrections"], here("corrections/")),
        (subscribe, tabs["subscribe"], here("suscribete/", "subscribe/")),
    )
    tabbar = "".join(f'<a href="{_e(u)}"{c}>{_e(t)}</a>' for u, t, c in tab_items)
    footer = strings["footer"]
    footer_ui = strings["footer_ui"]
    year = canonical[0:4] if canonical[:4].isdigit() else "2026"
    og = f'<meta property="og:image" content="{_e(og_image)}"><meta name="twitter:card" content="summary_large_image">' if og_image else ""
    structured = ""
    if json_ld:
        structured = '<script type="application/ld+json">' + json.dumps(json_ld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    # A tiny progressive enhancement: stale fallback and legacy fragment mapping.
    safeguard = r"""<script>(()=>{let b=document.querySelector('[data-edition-at]');if(b&&Date.now()-Date.parse(b.dataset.statusUpdatedAt||b.dataset.editionAt)>1296e5){b.hidden=false;b.dataset.editionState='DELAYED'}let m=location.hash.match(/^#\/brief\/(FCMO-[A-F0-9]{12})/);if(m)location.replace(document.documentElement.dataset.storyBase+m[1]+'.html')})()</script>"""
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
{structured}{agent_alternates(machine_alternates)}{extra_head}
</head>
<body class="{_e(body_class)}"><a class="skip-link" href="#main">{_e(strings['a11y']['skip_to_content'])}</a>
<header class="topbar surface-ink"><div class="frame topbar-in"><a class="brandmark" href="{_e(home)}" aria-label="{_e(strings['brand']['home_label'])}"><img class="brandmark-sym" src="{_e(brand_sym)}" alt="" width="28" height="28">FCMO AI</a>
<nav class="topnav" aria-label="{_e(strings['a11y']['primary_nav'])}">{topnav}</nav>
<nav class="langsel" aria-label="{_e(strings['a11y']['language_switcher'])}">{languages}</nav><a class="btn-cta" href="{_e(subscribe)}">{_e(tabs['subscribe'])}</a></div></header>
{status_banner}<main id="main" class="page-shell"{f' data-story-id="{_e(story_id)}"' if story_id else ''}>{breadcrumb}{body}</main>
<footer class="footbar surface-bone"><div class="frame"><p class="footbar-brand"><a href="{_e(home)}"><strong>FCMO AI</strong></a> · {_e(footer_ui['tagline'])}</p>
<nav class="footbar-links" aria-label="{_e(strings['a11y']['footer_navigation'])}"><a href="{_e(_url(base, locale_prefix+'about/'))}">{_e(footer['about'])}</a><a href="{_e(method)}">{_e(footer['method'])}</a><a href="{_e(corrections)}">{_e(footer['corrections'])}</a><a href="{_e(subscribe)}">{_e(tabs['subscribe'])}</a><a href="{_e(feeds)}">{_e(footer['feeds'])}</a><a href="{_e(status)}">{_e(footer['status'])}</a><a href="{_e(_url(base, locale_prefix+'privacy/'))}">{_e(footer['privacy'])}</a><a href="{_e(_url(base, locale_prefix+'license/'))}">{_e(footer['license'])}</a><a href="{_e(_url(base, locale_prefix+'disclaimer/'))}">{_e(footer['disclaimer'])}</a></nav>
<p class="footbar-fine">{_e(footer_ui['one_publication'])} {_e(footer['automated_notice'])}<br>{_e(footer['copyright'].format(year=year))}</p></div></footer>
<nav class="tabbar" aria-label="{_e(strings['a11y']['bottom_tabs'])}">{tabbar}</nav>{safeguard}</body></html>'''
