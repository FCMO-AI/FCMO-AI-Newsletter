"""Share kit page: why read the FCMO AI Newsletter, share cards and ready-to-post texts.

Every claim on this page is something a reader can check on the publication itself
(evidence grade on each story, the open-gaps column, the corrections page, the
automation disclosure, the three native languages, the open feeds). Nothing here
says "independent", "best" or quotes an error rate the publication has not measured.
"""

from html import escape
import re
from urllib.parse import quote

X_LIMIT = 280
X_URL_COST = 23  # X counts every link as 23 characters

COPY = {
    "en": {
        "kicker": "FCMO AI Newsletter · Share",
        "title": "The AI daily that shows how well each story is supported.",
        "dek": "Every story says what is demonstrated, what is not established and where the information comes from. It is free, daily, and written in English, Spanish and Chinese.",
        "why": "Why read it",
        "reasons": (
            ("Evidence on the page", "Each story carries an evidence grade, a confidence level and a count of its claims by kind of proof, so a strong result and a loose rumor never look the same."),
            ("What is not established", "Every story has a fixed place for open gaps and limitations. If a claim is only claimed and not verified, it says so."),
            ("Automation said out loud", "The stories are written by an automated research system and checked by deterministic gates. The page tells you that, and withdrawn stories stay listed with the reason."),
            ("Built to be followed", "Three native languages, plus RSS, Atom, JSON Feed and machine-readable data for each story, so you can read it, subscribe by feed or feed it to your own tools."),
        ),
        "record": "The public record today",
        "stories": "stories", "topics": "topics", "organizations": "organizations", "editions": "editions",
        "cards": "Cards to share",
        "cards_dek": "Open Graph cards: they appear automatically when you paste the link, and you can also download the image.",
        "card_brand": "The publication", "card_edition": "Latest edition", "download": "Download PNG",
        "texts": "Texts ready to post",
        "texts_dek": "They already include today's lead story and the link to the latest edition. Edit them freely.",
        "linkedin": "LinkedIn", "x": "X", "whatsapp": "WhatsApp",
        "copy": "Copy text", "copied": "Copied", "open": "Open in",
        "follow": "Follow it", "follow_dek": "Email signup is on the subscription page. Feeds work today with no account.",
        "follow_link": "Subscription options", "feeds": "Open feeds", "method": "How it is made",
        "today": "Today", "length": "characters",
        "post_linkedin": "Today in the FCMO AI Newsletter: {headline}\n\nWhat sets it apart: each story says how well it is supported, what is still unproven and where the information comes from. It is written by an automated research system, and says so on every story, with public corrections.\n\nFree, daily, in English, Spanish and Chinese.\n{url}",
        "post_x": "Today in FCMO AI Newsletter: {headline}\n\nEvery story says what is demonstrated and what is not. Daily, free, in English, Spanish and Chinese.\n{url}",
        "post_whatsapp": "I am sharing the FCMO AI Newsletter: an AI daily that shows how well each story is supported and what is still unproven. Today: {headline}\n{url}",
    },
    "es-419": {
        "kicker": "FCMO AI Newsletter · Comparte",
        "title": "El diario de IA que muestra qué tan sustentada está cada historia.",
        "dek": "Cada historia dice qué está demostrado, qué no está establecido y de dónde viene la información. Es gratis, diario y se publica en español, inglés y chino.",
        "why": "Por qué leerlo",
        "reasons": (
            ("La evidencia, a la vista", "Cada historia lleva un grado de evidencia, un nivel de confianza y el conteo de sus afirmaciones según el tipo de prueba. Un resultado sólido y un rumor suelto nunca se ven igual."),
            ("Lo que no está establecido", "Cada historia tiene un lugar fijo para los vacíos y las limitaciones. Si una afirmación sólo está declarada y no verificada, lo dice."),
            ("La automatización, dicha de frente", "Las historias las escribe un sistema automatizado de investigación y pasan por compuertas deterministas. La página te lo dice, y las historias retiradas siguen listadas con su motivo."),
            ("Hecho para seguirse", "Tres idiomas nativos, más RSS, Atom, JSON Feed y datos legibles por máquina de cada historia: léelo, suscríbete por feed o conéctalo a tus propias herramientas."),
        ),
        "record": "El registro público hoy",
        "stories": "historias", "topics": "temas", "organizations": "organizaciones", "editions": "ediciones",
        "cards": "Tarjetas para compartir",
        "cards_dek": "Tarjetas Open Graph: aparecen solas al pegar el enlace y también puedes descargar la imagen.",
        "card_brand": "La publicación", "card_edition": "Última edición", "download": "Descargar PNG",
        "texts": "Textos listos para publicar",
        "texts_dek": "Ya incluyen la historia principal de hoy y el enlace a la última edición. Edítalos con libertad.",
        "linkedin": "LinkedIn", "x": "X", "whatsapp": "WhatsApp",
        "copy": "Copiar texto", "copied": "Copiado", "open": "Abrir en",
        "follow": "Síguelo", "follow_dek": "El alta por correo está en la página de suscripción. Los feeds funcionan hoy, sin cuenta.",
        "follow_link": "Opciones de suscripción", "feeds": "Abrir feeds", "method": "Cómo se hace",
        "today": "Hoy", "length": "caracteres",
        "post_linkedin": "Hoy en la FCMO AI Newsletter: {headline}\n\nLo que la distingue: cada historia dice qué tan sustentada está, qué sigue sin demostrarse y de dónde viene la información. La escribe un sistema automatizado de investigación, y lo dice en cada nota, con correcciones públicas.\n\nGratis, diaria, en español, inglés y chino.\n{url}",
        "post_x": "Hoy en FCMO AI Newsletter: {headline}\n\nCada historia dice qué está demostrado y qué no. Diaria, gratis, en español, inglés y chino.\n{url}",
        "post_whatsapp": "Te comparto la FCMO AI Newsletter: un diario de IA que muestra qué tan sustentada está cada noticia y qué falta por demostrar. Hoy: {headline}\n{url}",
    },
    "zh-Hans": {
        "kicker": "FCMO AI Newsletter · 分享",
        "title": "展示每篇报道证据强度的 AI 日报。",
        "dek": "每篇报道都说明哪些已被证实、哪些尚未证实，以及信息来自哪里。免费、每日更新，提供英文、西班牙文和中文。",
        "why": "为什么值得读",
        "reasons": (
            ("证据直接摆在页面上", "每篇报道都有证据等级、置信度，以及按证明方式分类的主张数量，所以扎实的结果和零散的传闻看起来绝不一样。"),
            ("哪些尚未证实", "每篇报道都有固定位置列出未解之处与局限。如果某项主张只是声称、尚未核实，页面会直接说明。"),
            ("坦率说明自动化", "报道由自动化研究系统撰写，并经过确定性检查。页面会告诉你这一点，被撤回的报道也会连同原因继续列出。"),
            ("方便持续关注", "三种原生语言，另有 RSS、Atom、JSON Feed 以及每篇报道的机器可读数据：可以直接阅读、用订阅源关注，或接入你自己的工具。"),
        ),
        "record": "今天的公开记录",
        "stories": "篇报道", "topics": "个主题", "organizations": "家机构", "editions": "期",
        "cards": "分享卡片",
        "cards_dek": "Open Graph 卡片：粘贴链接时会自动出现，也可以下载图片。",
        "card_brand": "关于刊物", "card_edition": "最新一期", "download": "下载 PNG",
        "texts": "可直接发布的文字",
        "texts_dek": "已包含今天的头条和最新一期的链接，可自由修改。",
        "linkedin": "LinkedIn", "x": "X", "whatsapp": "WhatsApp",
        "copy": "复制文字", "copied": "已复制", "open": "打开",
        "follow": "关注", "follow_dek": "邮件订阅请见订阅页面。订阅源今天即可使用，无需账号。",
        "follow_link": "订阅方式", "feeds": "打开订阅源", "method": "制作方式",
        "today": "今天", "length": "字符",
        "post_linkedin": "今天的 FCMO AI Newsletter：{headline}\n\n它的不同之处：每篇报道都说明证据强度、哪些仍未证实以及信息来源。报道由自动化研究系统撰写，并在每篇中如实标明，同时公开更正记录。\n\n免费、每日更新，提供英文、西班牙文和中文。\n{url}",
        "post_x": "今天的 FCMO AI Newsletter：{headline}\n\n每篇报道都说明哪些已证实、哪些没有。每日更新，免费，英文、西班牙文、中文。\n{url}",
        "post_whatsapp": "分享 FCMO AI Newsletter：一份展示每篇报道证据强度、并标明哪些尚未证实的 AI 日报。今天：{headline}\n{url}",
    },
}


def x_length(text: str) -> int:
    """Length as X counts it: each http(s) URL costs 23 and each CJK character 2."""
    flat = re.sub(r"https?://\S+", "x" * X_URL_COST, text)
    return sum(2 if "\u1100" <= ch <= "\u11ff" or "\u2e80" <= ch <= "\ud7a3" or "\uf900" <= ch <= "\ufaff" or "\uff00" <= ch <= "\uff60" else 1 for ch in flat)


def _fit_x(template: str, headline: str, url: str) -> str:
    """Trim the headline until the X post fits; never trim the link."""
    text = template.format(headline=headline, url=url)
    while headline and x_length(text) > X_LIMIT:
        headline = headline[:-2].rstrip(" ,;:.") + "…" if len(headline) > 2 else ""
        text = template.format(headline=headline, url=url)
    return text


def posts(locale: str, headline: str, url: str) -> dict[str, str]:
    c = COPY[locale]
    return {
        "linkedin": c["post_linkedin"].format(headline=headline, url=url),
        "x": _fit_x(c["post_x"], headline, url),
        "whatsapp": c["post_whatsapp"].format(headline=headline, url=url),
    }


def intent_links(text: str, url: str) -> dict[str, str]:
    return {
        "linkedin": "https://www.linkedin.com/sharing/share-offsite/?url=" + quote(url, safe=""),
        "x": "https://twitter.com/intent/tweet?text=" + quote(text, safe=""),
        "whatsapp": "https://wa.me/?text=" + quote(text, safe=""),
    }


def render(*, locale: str, headline: str, edition_url: str, edition_date: str, brand_card: str, edition_card: str,
           stats: tuple[int, int, int, int], feeds_href: str, subscribe_href: str, method_href: str) -> str:
    c = COPY[locale]
    e = lambda value: escape(str(value), quote=True)
    texts = posts(locale, headline, edition_url)
    links = intent_links
    reasons = "".join(f'<li><span>0{n}</span><h3>{e(title)}</h3><p>{e(body)}</p></li>' for n, (title, body) in enumerate(c["reasons"], 1))
    labels = (c["stories"], c["topics"], c["organizations"], c["editions"])
    numbers = "".join(f'<li><strong>{value}</strong><span>{e(label)}</span></li>' for value, label in zip(stats, labels))
    cards = (
        f'<figure class="share-card"><img src="{e(brand_card)}" width="1200" height="630" loading="lazy" alt="{e(c["card_brand"])}: FCMO AI Newsletter">'
        f'<figcaption><span>{e(c["card_brand"])}</span><a href="{e(brand_card)}" download>{e(c["download"])}</a></figcaption></figure>'
        f'<figure class="share-card"><img src="{e(edition_card)}" width="1200" height="630" loading="lazy" alt="{e(c["card_edition"])} {e(edition_date)}: {e(headline)}">'
        f'<figcaption><span>{e(c["card_edition"])} · {e(edition_date)}</span><a href="{e(edition_card)}" download>{e(c["download"])}</a></figcaption></figure>'
    )
    blocks = []
    for key in ("linkedin", "x", "whatsapp"):
        text = texts[key]
        intent = links(text, edition_url)[key]
        rows = sum(max(1, -(-len(line) // 32)) for line in text.split("\n")) + 1
        count = x_length(text) if key == "x" else len(text)
        blocks.append(
            f'<article class="share-post" data-channel="{key}"><header><h3>{e(c[key])}</h3><span class="share-count">{count} {e(c["length"])}</span></header>'
            f'<textarea readonly rows="{rows}" id="post-{key}" aria-label="{e(c[key])}">{e(text)}</textarea>'
            f'<p class="share-actions"><button type="button" class="button" data-copy="post-{key}" data-done="{e(c["copied"])}">{e(c["copy"])}</button>'
            f'<a href="{e(intent)}" rel="noopener external" target="_blank">{e(c["open"])} {e(c[key])} ↗</a></p></article>'
        )
    return f'''<div class="share">
<section class="share-hero" aria-labelledby="share-title"><p class="section-kicker">{e(c["kicker"])}</p><h1 id="share-title">{e(c["title"])}</h1><p class="share-dek">{e(c["dek"])}</p></section>
<section class="share-why" aria-labelledby="why-title"><div class="share-head"><p class="section-kicker">FCMO AI / 01</p><h2 id="why-title">{e(c["why"])}</h2></div><ol>{reasons}</ol>
<div class="share-record"><p class="section-kicker">{e(c["record"])}</p><ul>{numbers}</ul></div></section>
<section class="share-cards" aria-labelledby="cards-title"><div class="share-head"><p class="section-kicker">FCMO AI / 02</p><h2 id="cards-title">{e(c["cards"])}</h2><p>{e(c["cards_dek"])}</p></div><div class="share-card-grid">{cards}</div></section>
<section class="share-texts" aria-labelledby="texts-title"><div class="share-head"><p class="section-kicker">FCMO AI / 03</p><h2 id="texts-title">{e(c["texts"])}</h2><p>{e(c["texts_dek"])}</p></div><div class="share-post-grid">{"".join(blocks)}</div></section>
<section class="share-follow" aria-labelledby="follow-title"><div><p class="section-kicker">FCMO AI / 04</p><h2 id="follow-title">{e(c["follow"])}</h2><p>{e(c["follow_dek"])}</p></div>
<p class="share-follow-links"><a class="button" href="{e(subscribe_href)}">{e(c["follow_link"])}</a><a href="{e(feeds_href)}">{e(c["feeds"])} →</a><a href="{e(method_href)}">{e(c["method"])} →</a></p></section>
</div>'''
