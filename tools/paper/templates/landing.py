"""FCMO entry with Javier's fCMO publication and an FCMO AI depth well."""

from html import escape

from tools.paper.routes import PRODUCT_NAMES
from .subscribe import subscribe_block


COPY = {
    "en": {
        "eyebrow": "FCMO · People, systems, software",
        "title": "Understand what moves. Build what lasts.",
        "intro": "A human letter for clearer decisions and a technical paper for the evidence behind them.",
        "letter": "fCMO · Javier's letters",
        "letter_dek": "Javier writes from the work of turning strategy into operating capacity. Start with a plain-language route through the ideas, then read the latest letter.",
        "start": "Start here",
        "latest": "Latest letter",
        "empty": "Javier's letters will appear here when published. Begin with the reading guide and the public research record today.",
        "record": "In the public record",
        "stories": "stories",
        "topics": "topics",
        "organizations": "organizations",
        "letter_path": "Explore Javier's letters",
        "community_path": "Community and conversation",
        "technical": "The technical paper",
        "technical_dek": "Matías and the FCMO AI Research Desk follow the public record: what changed, what the evidence supports, and what remains uncertain.",
        "today": "Open the latest technical edition",
        "subscribe": "Follow both sides of the publication",
        "subscribe_link": "Subscription options",
        "guide_title": "Find your way in",
        "guide_intro": "Choose the level of detail you need. Every technical story separates claims from evidence and open questions.",
        "step_one": "Start with the question",
        "step_one_body": "Javier's letters connect strategy to the decisions people make at work.",
        "step_two": "Check the record",
        "step_two_body": "The technical paper shows sources, limits and what remains unproven.",
        "step_three": "Follow the thread",
        "step_three_body": "Read the publication method and choose how to keep up.",
        "method": "How we work",
    },
    "es-419": {
        "eyebrow": "FCMO · Personas, sistemas, software",
        "title": "Entiende lo que cambia. Construye lo que permanece.",
        "intro": "Una carta humana para decidir con claridad y un diario técnico para examinar la evidencia.",
        "letter": "fCMO · Cartas de Javier",
        "letter_dek": "Javier escribe desde la práctica de convertir la estrategia en capacidad operativa. Empieza por una ruta clara y luego lee la carta más reciente.",
        "start": "Empieza aquí",
        "latest": "Carta más reciente",
        "empty": "Las cartas de Javier aparecerán aquí cuando se publiquen. Hoy puedes comenzar con la guía de lectura y el registro público de investigación.",
        "record": "En el registro público",
        "stories": "historias",
        "topics": "temas",
        "organizations": "organizaciones",
        "letter_path": "Explora las cartas de Javier",
        "community_path": "Comunidad y conversación",
        "technical": "El diario técnico",
        "technical_dek": "Matías y la Mesa de Investigación FCMO AI siguen el registro público: qué cambió, qué sostiene la evidencia y qué sigue incierto.",
        "today": "Abrir la edición técnica más reciente",
        "subscribe": "Sigue las dos partes de la publicación",
        "subscribe_link": "Opciones de suscripción",
        "guide_title": "Encuentra tu camino",
        "guide_intro": "Elige el nivel de detalle que necesitas. Cada historia técnica distingue afirmaciones, evidencia y preguntas abiertas.",
        "step_one": "Empieza por la pregunta",
        "step_one_body": "Las cartas de Javier conectan la estrategia con las decisiones del trabajo real.",
        "step_two": "Examina el registro",
        "step_two_body": "El diario técnico muestra fuentes, límites y lo que falta demostrar.",
        "step_three": "Sigue el hilo",
        "step_three_body": "Conoce el método editorial y elige cómo mantenerte al día.",
        "method": "Cómo trabajamos",
    },
    "zh-Hans": {
        "eyebrow": "FCMO · 人员、系统、软件",
        "title": "看清变化，构建长久能力。",
        "intro": "一封帮助清晰决策的来信，一份追溯证据的技术日报。",
        "letter": "fCMO · Javier 来信",
        "letter_dek": "Javier 从实践出发，讲述如何将战略转化为持续运作的能力。先从清晰的入门路径开始，再读最新来信。",
        "start": "从这里开始",
        "latest": "最新来信",
        "empty": "Javier 的来信发布后会出现在这里。现在可以先从阅读指南和公开研究记录开始。",
        "record": "公开记录",
        "stories": "篇报道",
        "topics": "个主题",
        "organizations": "个机构",
        "letter_path": "浏览 Javier 的来信",
        "community_path": "社群与交流",
        "technical": "技术日报",
        "technical_dek": "Matías 与 FCMO AI 研究编辑台追踪公开记录：发生了什么、证据支持什么、还有哪些未知。",
        "today": "阅读最新技术版",
        "subscribe": "关注刊物的两个部分",
        "subscribe_link": "订阅方式",
        "guide_title": "从这里读起",
        "guide_intro": "按你需要的深度阅读。每篇技术报道都会区分主张、证据和未解问题。",
        "step_one": "先提出问题",
        "step_one_body": "Javier 的来信把战略与工作中的真实决策联系起来。",
        "step_two": "核查记录",
        "step_two_body": "技术日报列出来源、限制和仍待证明的部分。",
        "step_three": "沿线索继续",
        "step_three_body": "了解编辑方法，并选择关注方式。",
        "method": "工作方法",
    },
}


def render(*, locale: dict, home: str, technical: str, about: str, subscribe: str,
           lead: str, top: str, cartas: str, stats: tuple[int, int, int] = (0, 0, 0),
           feature: dict | None = None) -> str:
    c = COPY[locale["code"]]
    e = lambda value: escape(str(value), quote=True)
    letter = cartas or f'<div class="landing-empty"><p class="section-kicker">fCMO / Javier</p><h3>{e(c["latest"])}</h3><p>{e(c["empty"])}</p><a href="{e(home)}cartas/">{e(c["letter_path"])} →</a></div>'
    letter_slot = ' data-slot="cartas"' if cartas else ""
    featured_report = ""
    if feature:
        featured_report = (
            '<article class="landing-feature story-card" style="grid-column:1/-1">'
            f'<p class="section-kicker">FCMO AI · {e(feature["label"])}</p>'
            '<figure class="hero">'
            f'<a href="{e(feature["href"])}"><img src="{e(feature["image"])}" '
            f'alt="{e(feature["alt"])}" width="1200" height="630" loading="eager"></a>'
            f'<figcaption>{e(feature["credit"])}</figcaption></figure>'
            f'<h2><a href="{e(feature["href"])}">{e(feature["title"])}</a></h2>'
            f'<p class="story-meta"><time datetime="{e(feature["datetime"])}">{e(feature["date"])}</time></p>'
            '</article>'
        )
    lead = lead.replace("<h1 ", "<h3 ", 1).replace("</h1>", "</h3>", 1)
    return f'''<div class="landing">
<section class="landing-intro" aria-labelledby="landing-title"><p class="section-kicker">{e(c['eyebrow'])}</p><h1 id="landing-title">{e(c['title'])}</h1><p class="landing-dek">{e(c['intro'])}</p><div class="landing-jump"><a href="{e(home)}cartas/">{e(c['letter'])} <span aria-hidden="true">↗</span></a><a href="{e(technical)}">FCMO AI <span aria-hidden="true">↗</span></a></div><div class="landing-record" aria-label="{e(c['record'])}">{featured_report}<span>{e(c['record'])}</span><strong>{stats[0]} <small>{e(c['stories'])}</small></strong><strong>{stats[1]} <small>{e(c['topics'])}</small></strong><strong>{stats[2]} <small>{e(c['organizations'])}</small></strong></div></section>
<section class="landing-letters" id="letters" aria-labelledby="letters-title"><div class="landing-section-head"><p class="section-kicker">01 / fCMO · Javier</p><h2 id="letters-title">{e(c['letter'])}</h2><p>{e(c['letter_dek'])}</p><div class="landing-actions"><a class="button" href="{e(home)}empieza/">{e(c['start'])} <span aria-hidden="true">↗</span></a><a href="{e(home)}comunidad/">{e(c['community_path'])} →</a></div></div><div class="landing-letter-feed"{letter_slot}>{letter}</div></section>
<section class="landing-guide" id="start-here" aria-labelledby="guide-title"><div><p class="section-kicker">FCMO / 00</p><h2 id="guide-title">{e(c['guide_title'])}</h2><p>{e(c['guide_intro'])}</p></div><ol><li><span>01</span><h3>{e(c['step_one'])}</h3><p>{e(c['step_one_body'])}</p><a href="{e(home)}cartas/">{e(c['letter'])} →</a></li><li><span>02</span><h3>{e(c['step_two'])}</h3><p>{e(c['step_two_body'])}</p><a href="{e(technical)}">{e(c['technical'])} →</a></li><li><span>03</span><h3>{e(c['step_three'])}</h3><p>{e(c['step_three_body'])}</p><a href="{e(about)}">{e(c['method'])} →</a></li></ol></section>
<section class="landing-technical" id="technical" aria-labelledby="technical-title"><div class="technical-intro"><p class="section-kicker">02 / FCMO AI · Matías</p><h2 id="technical-title">{e(c['technical'])}</h2><p>{e(c['technical_dek'])}</p><a class="button" href="{e(technical)}">{e(c['today'])} <span aria-hidden="true">↗</span></a></div><div class="front-grid technical-grid">{lead}<aside class="top-stories">{top}</aside></div></section>
<section class="landing-subscribe" aria-labelledby="follow-title"><div><p class="section-kicker">fCMO + FCMO AI</p><h2 id="follow-title">{e(c['subscribe'])}</h2><a href="{e(subscribe)}">{e(c['subscribe_link'])} →</a></div>{subscribe_block('letter', locale['code'])}</section></div>'''
