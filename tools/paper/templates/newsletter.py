"""The human reading path: Javier's letters, a beginner guide and community."""

from html import escape


COPY = {
    "en": {
        "letters": "Letters from Javier", "letters_dek": "A human view of the decisions behind durable work. Read the published letters here, then follow a topic into the public research record.", "letters_shelf": "The letters shelf",
        "guide": "Start with the question", "guide_dek": "A short route from a useful question to the evidence beneath a technical headline.",
        "community": "A place for the conversation", "community_dek": "The letters invite a slower exchange about what to do with new ideas. Membership opens when the community is ready.",
        "reading": "Three ways in", "first": "Read the situation", "first_body": "What changed, for whom, and when? Begin with the plain-language summary before judging the claim.",
        "second": "Separate evidence from possibility", "second_body": "A strong signal and a large potential impact answer different questions. Look for sources, limits and remaining unknowns.",
        "third": "Decide what follows", "third_body": "Keep the question open when the record is incomplete. Follow the topic, then return as evidence changes.",
        "record": "From the public record", "next": "Continue reading", "latest": "Recent technical reporting", "empty": "No letter is published yet. This guide and the technical record are available now.", "topics": "Follow a subject", "topic_count": "stories",
        "subscribe": "Choose how to follow", "subscribe_body": "Email registration opens when the publication is ready. The public feeds already provide an open way to follow the daily.",
        "letter_link": "Letters", "guide_link": "Beginner guide", "community_link": "Community", "technical_link": "Technical daily", "feed_link": "Open feeds", "subscribe_link": "Subscription options",
    },
    "es-419": {
        "letters": "Cartas de Javier", "letters_dek": "Una mirada humana a las decisiones que sostienen el trabajo. Lee aquí las cartas publicadas y sigue un tema hasta el registro de investigación.", "letters_shelf": "Archivo de cartas",
        "guide": "Empieza por la pregunta", "guide_dek": "Una ruta breve desde una pregunta útil hasta la evidencia detrás de un titular técnico.",
        "community": "Un lugar para conversar", "community_dek": "Las cartas invitan a pensar con calma qué hacer con las ideas nuevas. La membresía abrirá cuando la comunidad esté lista.",
        "reading": "Tres formas de entrar", "first": "Lee la situación", "first_body": "¿Qué cambió, para quién y cuándo? Empieza por el resumen claro antes de juzgar la afirmación.",
        "second": "Separa evidencia y posibilidad", "second_body": "Una señal sólida y un gran impacto potencial responden preguntas distintas. Busca fuentes, límites y dudas pendientes.",
        "third": "Decide qué sigue", "third_body": "Mantén abierta la pregunta si el registro está incompleto. Sigue el tema y vuelve cuando cambie la evidencia.",
        "record": "Del registro público", "next": "Sigue leyendo", "latest": "Cobertura técnica reciente", "empty": "Aún no se ha publicado una carta. La guía y el registro técnico ya están disponibles.", "topics": "Sigue un tema", "topic_count": "historias",
        "subscribe": "Elige cómo seguir", "subscribe_body": "El alta por correo abrirá cuando la publicación esté lista. Los feeds públicos ya permiten seguir el diario.",
        "letter_link": "Cartas", "guide_link": "Guía inicial", "community_link": "Comunidad", "technical_link": "Diario técnico", "feed_link": "Abrir feeds", "subscribe_link": "Opciones de suscripción",
    },
    "zh-Hans": {
        "letters": "Javier 来信", "letters_dek": "从人的角度理解支持长期工作的决策。在这里阅读已发表的来信，再沿着主题进入公开研究记录。", "letters_shelf": "来信目录",
        "guide": "从问题开始", "guide_dek": "从一个有用的问题出发，逐步读到技术标题背后的证据。",
        "community": "继续交流", "community_dek": "来信邀请读者慢下来，讨论如何使用新想法。社群准备就绪后将开放会员。",
        "reading": "三步开始", "first": "先看背景", "first_body": "发生了什么变化？影响谁？何时发生？先读清晰摘要，再判断主张。",
        "second": "区分证据与可能性", "second_body": "信号强弱与潜在影响是两个问题。查看来源、限制及未解之处。",
        "third": "决定下一步", "third_body": "记录不完整时保留疑问。关注主题，在证据变化后回来查看。",
        "record": "公开记录精选", "next": "继续阅读", "latest": "近期技术报道", "empty": "目前尚无已发表的来信。阅读指南和技术记录现已开放。", "topics": "关注主题", "topic_count": "篇报道",
        "subscribe": "选择关注方式", "subscribe_body": "出版准备就绪后将开放电子邮件注册。公开订阅源现已可用于关注日报。",
        "letter_link": "来信", "guide_link": "入门指南", "community_link": "社群", "technical_link": "技术日报", "feed_link": "打开订阅源", "subscribe_link": "订阅方式",
    },
}

TOPIC_LABELS = {
    "es-419": {"post-training": "posentrenamiento", "multi-token-prediction": "predicción de varios tokens", "sparse-attention": "atención dispersa", "robotics": "robótica", "reward-hacking": "manipulación de recompensas", "reinforcement-learning": "aprendizaje por refuerzo", "frontier-models": "modelos de frontera", "world-models": "modelos del mundo"},
    "zh-Hans": {"post-training": "后训练", "multi-token-prediction": "多词元预测", "sparse-attention": "稀疏注意力", "robotics": "机器人技术", "reward-hacking": "奖励操纵", "reinforcement-learning": "强化学习", "frontier-models": "前沿模型", "world-models": "世界模型"},
}


def render(kind: str, *, locale: str, root: str, technical: str, cards: str, cartas: str = "",
           topics: list[tuple[str, int, str]] | None = None) -> tuple[str, str, str]:
    """Return title, description and HTML using only source-controlled copy and cards."""
    c = COPY[locale]
    e = lambda value: escape(str(value), quote=True)
    title, dek = c[kind], c[kind + "_dek"]
    links = f'<nav class="newsletter-path" aria-label="{e(c["next"])}"><a href="{e(root)}cartas/">{e(c["letter_link"])} ↗</a><a href="{e(root)}empieza/">{e(c["guide_link"])} ↗</a><a href="{e(root)}comunidad/">{e(c["community_link"])} ↗</a><a href="{e(technical)}">{e(c["technical_link"])} ↗</a></nav>'
    head = f'<header class="newsletter-hero"><p class="section-kicker">fCMO / Javier</p><h1>{e(title)}</h1><p>{e(dek)}</p>{links}</header>'
    steps = (f'<section class="newsletter-steps" aria-labelledby="reading-title"><div class="newsletter-section-head"><p class="section-kicker">fCMO / 01—03</p><h2 id="reading-title">{e(c["reading"])}</h2></div><ol>'
             + "".join(f'<li><span>0{n}</span><h3>{e(c[key])}</h3><p>{e(c[key + "_body"])}</p></li>' for n, key in enumerate(("first", "second", "third"), 1)) + '</ol></section>')
    record = f'<section class="newsletter-record"><div class="newsletter-section-head"><p class="section-kicker">FCMO AI</p><h2>{e(c["record"])}</h2><a href="{e(technical)}">{e(c["technical_link"])} ↗</a></div><div class="card-row">{cards}</div></section>' if cards else ""
    topics = topics or []
    topic_list = (f'<section class="newsletter-topics"><div class="newsletter-section-head"><p class="section-kicker">FCMO AI / INDEX</p><h2>{e(c["topics"])}</h2></div><ol>'
                  + "".join(f'<li><a href="{e(root)}topic/{e(slug)}/"><span{(" lang=\"en\"" if locale != "en" and slug not in TOPIC_LABELS.get(locale, {}) else "")}>{e(TOPIC_LABELS.get(locale, {}).get(slug, name))}</span><b>{count} {e(c["topic_count"])}</b></a><i style="--topic-share:{count/max(1,topics[0][1]):.3f}" aria-hidden="true"></i></li>' for name, count, slug in topics)
                  + '</ol></section>') if topics else ""
    if kind == "letters":
        featured = f'<section class="newsletter-letter-list"><div class="newsletter-section-head"><p class="section-kicker">fCMO / Javier</p><h2>{e(c["letters_shelf"])}</h2></div>{cartas or f"<p>{e(c['empty'])}</p>"}</section>'
        body = head + featured + steps + record + topic_list
    elif kind == "guide":
        body = head + steps + record + topic_list
    elif kind == "community":
        body = head + steps + f'<section class="newsletter-follow"><p class="section-kicker">fCMO / FCMO AI</p><h2>{e(c["subscribe"])}</h2><p>{e(c["subscribe_body"])}</p><a href="{e(root)}suscribete/">{e(c["subscribe_link"])} ↗</a><a href="{e(root)}feeds/">{e(c["feed_link"])} ↗</a></section>' + record + topic_list
    else:
        raise ValueError(f"unknown newsletter page: {kind}")
    return title, dek, f'<div class="newsletter-page">{body}</div>'


def subscription_tail(*, locale: str, root: str, technical: str, cards: str) -> str:
    """Give readers a useful path while email registration is inactive."""
    c = COPY[locale]
    e = lambda value: escape(str(value), quote=True)
    return (f'<section class="newsletter-record subscribe-reading"><div class="newsletter-section-head">'
            f'<p class="section-kicker">FCMO AI / fCMO</p><h2>{e(c["record"])}</h2>'
            f'<a href="{e(technical)}">{e(c["technical_link"])} ↗</a></div>'
            f'<div class="card-row">{cards}</div><nav class="newsletter-path" aria-label="{e(c["next"])}">'
            f'<a href="{e(root)}cartas/">{e(c["letter_link"])} ↗</a>'
            f'<a href="{e(root)}empieza/">{e(c["guide_link"])} ↗</a></nav></section>')
