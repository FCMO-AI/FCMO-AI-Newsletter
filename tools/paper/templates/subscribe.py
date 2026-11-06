"""Subscription copy and stable block API for the static publication.

The selected provider owns subscription delivery and confirmation. Public
configuration supplies the action URL; credentials never enter the static form.
"""
from __future__ import annotations

from html import escape
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

CONFIG = Path(__file__).resolve().parents[3] / "community/config/subscriptions.json"
_LOCALES = {
    "en": {"soon": "Subscriptions are coming soon", "ready": "Choose how to follow", "intro": "One publication. Follow it your way.", "closed": "Email signup opens at launch. No information is sent from this page.", "language": "", "cta": "Choose my emails", "manage": "Change preferences or leave at any time in your account.", "rss": "RSS", "json": "JSON feed"},
    "es-419": {"soon": "Las suscripciones llegarán pronto", "ready": "Elige cómo seguirnos", "intro": "Una sola publicación. Síguela a tu manera.", "closed": "El alta por correo abre en el lanzamiento. Esta página no envía ningún dato.", "language": "", "cta": "Elegir mis correos", "manage": "Cambia tus preferencias o date de baja en cualquier momento desde tu cuenta.", "rss": "RSS", "json": "Feed JSON"},
    "zh-Hans": {"soon": "订阅即将开放", "ready": "选择关注方式", "intro": "一份刊物，随你的方式关注。", "closed": "电子邮件订阅将在发布时开放。此页面不会提交任何数据。", "language": "", "cta": "选择邮件", "manage": "你可以随时在账户中更改偏好或退订。", "rss": "RSS", "json": "JSON 订阅源"},
}
def subscription_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def ghost_signup_url(value: str | None) -> str | None:
    """Accept only a clean HTTPS or loopback origin; never reflect query secrets."""
    if not value:
        return None
    try:
        parts = urlsplit(value.strip())
        if not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
            return None
        if parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1", "::1"}):
            return None
        if parts.path not in {"", "/"}:
            return None
        return urlunsplit((parts.scheme, parts.netloc, "/", "", "/portal/signup"))
    except ValueError:
        return None


def subscribe_block(zone: str, locale: str, *, base: str = "/FCMO-AI-Newsletter/", path_prefix: str | None = None,
                    ghost_url: str | None = None, page: bool = False) -> str:
    """Render the landing/page CTA for the one publication. ``zone`` is ``letter``, ``paper``, or ``all``."""
    if zone not in {"letter", "paper", "all"}:
        raise ValueError("unknown subscription zone")
    from tools.email_providers import signup_form
    form = None
    if os.environ.get('FCMO_EMAIL_ENABLED') != 'false':
        try:
            form = signup_form(os.environ, locale)
        except ValueError:
            pass
    if form is not None and zone in {'paper', 'all'}:
        return diario_form(locale, base, form, page)
    config = subscription_config()
    copy = _LOCALES.get(locale, _LOCALES["en"])
    configured_url = ghost_url if ghost_url is not None else os.environ.get("GHOST_URL") or os.environ.get("GHOST_PORTAL_URL")
    if configured_url and configured_url.endswith("#/portal/signup"):
        configured_url = configured_url.split("#", 1)[0]
    ghost = ghost_signup_url(configured_url)
    active = ghost is not None and locale in config["languages"]["signup_locales"]
    root = base.rstrip("/") + "/" + (path_prefix if path_prefix is not None else {"es-419": "es/", "zh-Hans": "zh/"}.get(locale, ""))
    action = (f'<p><a class="button" href="{escape(ghost, quote=True)}" rel="external noopener" data-ghost-portal="signup">{escape(copy["cta"])}</a></p>' if active else
              f'<p class="subscription-state"><strong>{escape(copy["closed"])}</strong></p>')
    title = copy["ready"] if active else copy["soon"]
    manage = copy["manage"] if active else {"en": "When signup opens, you can change or leave at any time.", "es-419": "Cuando abra el alta, podrás cambiar tus preferencias o darte de baja cuando quieras.", "zh-Hans": "开放订阅后，你可以随时更改偏好或退订。"}.get(locale, copy["manage"])
    tag = "h1" if page else "h2"
    wrapper = "subscribe-page" if page else "subscribe-card"
    heading = f'<{tag} class="page-title">{escape(title)}</{tag}>'
    # The headline "One publication. Follow it your way." belongs to the page; the home card sits under its own
    # headline and keeps only state, language and feeds, so no sentence is printed twice.
    embedded = zone == "all" and not page
    intro = "" if embedded else f'<p>{escape(copy["intro"])}</p>'
    manage_line = "" if embedded else f'<p>{escape(manage)}</p>'
    language = f'<p>{escape(copy["language"])}</p>' if copy["language"] and not active else ""
    return (f'<section class="{wrapper} subscribe-v2" data-subscribe-zone="{zone}" data-subscribe-state="{"active" if active else "launch"}">'
            f'<p class="section-kicker">FCMO AI</p>{heading}{intro}'
            f'{action}{manage_line}'
            f'{language}<ul class="community-options">'
            f'<li><a href="{escape(root + "feed.xml", quote=True)}">{escape(copy["rss"])}</a></li>'
            f'<li><a href="{escape(root + "feed.atom", quote=True)}">Atom</a></li>'
            f'<li><a href="{escape(root + "feed.json", quote=True)}">{escape(copy["json"])}</a></li></ul></section>')


# The three evidence classes are the publication's own method (see i18n `proof`); the form repeats them so
# the page that asks for an address already says what the address will receive. Labels and descriptions are
# the site's published strings, never a promise about a specific edition.
_PROOF = {
    'en': {'lead': 'Every story separates three things, in this order, before the long read.',
           'shown': ('Shown', 'What a primary source demonstrates, and how we can check it.'),
           'claimed': ('Claimed', 'What a source says without proof we could verify.'),
           'gap': ('Not established', 'What nobody has shown yet, and what the source cannot say.'),
           'langs': 'Edition language', 'step_email': 'Where should it arrive?', 'step_consent': 'Your consent',
           'fallback_error': 'Open the signup page instead'},
    'es-419': {'lead': 'Cada historia separa tres cosas, en este orden, antes de la lectura larga.',
               'shown': ('Demostrado', 'Lo que una fuente primaria demuestra y cómo podemos comprobarlo.'),
               'claimed': ('Afirmado', 'Lo que una fuente afirma sin una prueba que podamos verificar.'),
               'gap': ('No establecido', 'Lo que nadie ha demostrado todavía y lo que la fuente no puede decir.'),
               'langs': 'Idioma de la edición', 'step_email': '¿Adónde debe llegar?', 'step_consent': 'Tu consentimiento',
               'fallback_error': 'Abrir la página de suscripción'},
    'zh-Hans': {'lead': '每篇报道在长文之前，按这个顺序区分三件事。',
                'shown': ('已展示', '一手来源所展示的内容，以及我们如何核查。'),
                'claimed': ('仅声称', '来源所称、但我们无法核实的内容。'),
                'gap': ('尚未确立', '尚无人展示的内容，以及来源无法说明的部分。'),
                'langs': '版本语言', 'step_email': '发送到哪里？', 'step_consent': '你的同意',
                'fallback_error': '改用订阅页面'},
}


def diario_form(locale, base, form, page=False):
    from .subscription_states import COPY, PREFIX, LANGUAGE, state_page
    copy = COPY[locale]; prefix = PREFIX[locale]; extra = _PROOF[locale]
    root = base.rstrip('/')+'/'+prefix
    options = ''.join('<option value="'+v+'"'+(' selected' if v==locale else '')+'>'+label+'</option>' for v,label in (('en','English'),('es-419','Español'),('zh-Hans','简体中文')))
    language = f'<p class="sub-pick"><label>{escape(LANGUAGE[locale])} <select name="locale">{options}</select></label></p>'
    switcher = ''
    if form.fixed_locale:
        # One form per language: the control navigates to that language's own page and form.
        items = ''.join(
            (f'<span class="sub-lang" aria-current="true" lang="{loc}">{LANGUAGE[loc]}</span>' if loc == locale else
             f'<a class="sub-lang" href="{escape(base.rstrip("/") + "/" + PREFIX[loc] + "subscribe/")}" hreflang="{loc}" lang="{loc}">{LANGUAGE[loc]}</a>')
            for loc in PREFIX)
        switcher = f'<nav class="sub-langs" aria-label="{escape(extra["langs"], quote=True)}"><span class="sub-label">{escape(extra["langs"])}</span><span class="sub-lang-set">{items}</span></nav>'
        language = ''
    fallback = (f'<noscript><p class="sub-fine"><a href="{escape(form.fallback_url,quote=True)}" rel="external noopener">{copy["fallback"]}</a></p></noscript>' if form.fallback_url else '')
    # Visible only if the opaque POST fails: the hosted page is the one route that always shows the real outcome.
    error_link = (f'<a class="sub-error-link" href="{escape(form.fallback_url,quote=True)}" rel="external noopener" hidden>{escape(extra["fallback_error"])}</a>' if form.fallback_url else '')
    tag = 'h1' if page else 'h2'
    wrapper = 'subscribe-page' if page else 'subscribe-card'
    confirmation = (' data-email-confirmation="opaque"' if
                    re.fullmatch(r'https://app\.kit\.com/forms/[1-9][0-9]*/subscriptions', form.action) else '')
    proof = ''.join(f'<li class="sub-proof-{k}"><span class="sub-mark sub-mark-{k}" aria-hidden="true"></span>'
                    f'<strong>{escape(extra[k][0])}</strong><span>{escape(extra[k][1])}</span></li>' for k in ('shown', 'claimed', 'gap'))
    plate = (f'<div class="sub-plate" aria-hidden="true"><img src="{escape(base.rstrip("/") + "/assets/img/d-plates/d-piedra-grieta.webp")}" '
             'alt="" width="1800" height="600" loading="lazy" decoding="async"></div>')
    stop = '。' if locale == 'zh-Hans' else '.'
    notice = (f'<aside class="sub-notice" data-sub-notice><span class="sub-label">{escape(copy["notice_h"])}</span><ul>'
              + ''.join(f'<li>{escape(t)}</li>' for t in copy['notice']) + '</ul></aside>')
    return (f'<section class="subscribe-v2 {wrapper} sub-experience" data-subscribe-state="active" data-state="idle">'
            f'<div data-sub-idle class="sub-grid"><div class="sub-story"><div class="sub-copy">'
            f'<p class="section-kicker sub-kicker">{copy["kicker"]}</p><{tag} class="page-title">{copy["title"]}</{tag}><p class="sub-lede">{copy["lede"]}</p>'
            f'</div><div class="sub-proof"><p class="sub-label">{escape(extra["lead"])}</p><ol>{proof}</ol></div>{plate}</div>'
            f'<div class="sub-ledger">{switcher}'
            f'<form method="post" data-email-form{confirmation} data-email-locale="{locale}" action="{escape(form.action,quote=True)}" data-busy="{copy["busy"]}" data-error="{escape(copy["error"], quote=True)}">'
            f'{language}'
            f'<div class="sub-step"><span class="sub-num" aria-hidden="true">01</span><div class="sub-step-body">'
            f'<label class="sub-field"><span class="sub-label">{copy["email"]}</span><input type="email" name="{escape(form.email_field,quote=True)}" autocomplete="email" maxlength="254" placeholder="{copy["placeholder"]}" required></label></div></div>'
            f'<div class="sub-step"><span class="sub-num" aria-hidden="true">02</span><div class="sub-step-body">'
            f'<label class="sub-consent"><input type="checkbox" name="consent" value="yes" required><span>{copy["consent"]} <a href="{escape(root + "privacy/")}">{copy["privacy"]}</a>{stop}</span></label></div></div>'
            '<input type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" hidden>'
            f'<button class="button sub-submit" type="submit">{copy["button"]}</button>'
            f'<p class="sub-error" role="alert" hidden></p>{error_link}</form>'
            f'<p class="sub-fine">{copy["fine"]}</p>{notice}{fallback}'
            f'<p class="sub-fine"><a href="{escape(form.privacy_url,quote=True)}">{copy["complete"]}</a></p></div></div>'
            f'<div data-sub-pending hidden aria-live="polite">{state_page(locale, "pending", base, tag=tag)}'
            f'<p class="sub-retry"><button type="button" data-sub-retry>{escape(copy["help"])}</button></p></div></section>')
