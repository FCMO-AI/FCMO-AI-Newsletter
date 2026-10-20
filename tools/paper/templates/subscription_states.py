"""Native subscription presentation; Kit owns confirmation and suppression."""
from html import escape

PREFIX = {'en': '', 'es-419': 'es/', 'zh-Hans': 'zh/'}
LANGUAGE = {'en': 'English', 'es-419': 'Español', 'zh-Hans': '简体中文'}
COPY = {
    'en': {
        'kicker': 'Free · Daily', 'title': 'Get the FCMO AI Newsletter',
        'lede': 'One short briefing a day on what changed in AI: what happened, the evidence, and what is still unproven.',
        'email': 'Email address', 'placeholder': 'you@example.com', 'consent': 'I want to receive the FCMO AI Newsletter and have read the',
        'privacy': 'privacy notice', 'complete': 'Complete privacy notice', 'button': 'Subscribe', 'busy': 'Sending…',
        'fine': 'We email you once to confirm. Then one edition a day when fresh. Unsubscribe in one click.',
        'language': 'This form is for the English edition. Also in', 'fallback': 'Open the signup page',
        'error': 'We could not confirm submission. Check your inbox or try again in a moment.',
        'pending_kicker': 'One step left', 'pending': 'Check your inbox',
        'pending_body': 'If your request was received, a confirmation link will arrive by email. Confirm to subscribe. Until then, no editions are sent.',
        'help': 'Nothing after a few minutes? Look in spam or promotions, then try another address.',
        'done_kicker': 'Confirmed', 'done': 'You’re subscribed', 'done_body': 'After email confirmation, the next fresh edition will arrive in your inbox. Until then, today’s is here.',
        'today': 'Read today’s edition', 'archive': 'Browse the archive',
        'unsub_kicker': 'Unsubscribed', 'unsub': 'You’re unsubscribed',
        'unsub_body': 'After the provider confirms your unsubscribe request, no further editions will be sent. The newspaper remains free to read.',
        'again': 'Subscribe again',
    },
    'es-419': {
        'kicker': 'Gratis · Diario', 'title': 'Recibe la Newsletter de FCMO AI',
        'lede': 'Un resumen breve al día de lo que cambió en IA: qué pasó, la evidencia y lo que aún no está comprobado.',
        'email': 'Correo electrónico', 'placeholder': 'tu@correo.com', 'consent': 'Quiero recibir la Newsletter de FCMO AI y he leído el',
        'privacy': 'aviso de privacidad', 'complete': 'Aviso integral', 'button': 'Suscribirme', 'busy': 'Enviando…',
        'fine': 'Te escribimos una vez para confirmar. Después, una edición al día cuando haya novedades verificadas. Baja en un clic.',
        'language': 'Este formulario es para la edición en español. También en', 'fallback': 'Abrir la página de suscripción',
        'error': 'No pudimos confirmar el envío de la solicitud. Revisa tu bandeja o inténtalo de nuevo en un momento.',
        'pending_kicker': 'Falta un paso', 'pending': 'Revisa tu bandeja',
        'pending_body': 'Si se recibió tu solicitud, te llegará un enlace de confirmación por correo. Confirma para suscribirte. Hasta entonces no enviaremos ediciones.',
        'help': '¿Nada tras unos minutos? Mira en spam o promociones y prueba con otra dirección.',
        'done_kicker': 'Confirmado', 'done': 'Ya estás suscrito', 'done_body': 'Después de confirmar tu correo, la próxima edición con novedades llegará a tu bandeja. Mientras tanto, la de hoy está aquí.',
        'today': 'Leer la edición de hoy', 'archive': 'Ver el archivo',
        'unsub_kicker': 'Baja confirmada', 'unsub': 'Ya estás dado de baja',
        'unsub_body': 'Después de que el proveedor confirme tu baja, no recibirás más ediciones. El periódico sigue disponible gratis.',
        'again': 'Suscribirme de nuevo',
    },
    'zh-Hans': {
        'kicker': '免费 · 每日', 'title': '订阅 FCMO AI Newsletter',
        'lede': '每天一份简报：人工智能发生了什么、证据是什么、哪些仍未证实。',
        'email': '邮箱地址', 'placeholder': 'you@example.com', 'consent': '我希望收到 FCMO AI Newsletter，并已阅读',
        'privacy': '隐私声明', 'complete': '完整隐私声明', 'button': '订阅', 'busy': '正在提交…',
        'fine': '我们会先发一封确认邮件；有已核实的新内容时，每天最多一期。一键退订。',
        'language': '此表单用于简体中文版。也有', 'fallback': '打开订阅页面',
        'error': '无法确认申请是否已提交。请查看邮箱，或稍后重试。',
        'pending_kicker': '还差一步', 'pending': '请查收邮件',
        'pending_body': '如果申请已收到，确认链接将发送到你的邮箱。点击确认后才完成订阅；在此之前不会发送任何一期。',
        'help': '几分钟后仍未收到？请查看垃圾邮件或促销邮件，或换一个邮箱。',
        'done_kicker': '已确认', 'done': '订阅成功', 'done_body': '确认邮箱后，下一期有新内容的简报将发送到你的邮箱。在此之前，可以先读今天这一期。',
        'today': '阅读今天这一期', 'archive': '浏览往期',
        'unsub_kicker': '已退订', 'unsub': '你已退订',
        'unsub_body': '服务商确认退订后，你将不再收到后续邮件。你仍可免费阅读报纸。', 'again': '重新订阅',
    },
}

def state_page(locale, state, base, *, tag='h1'):
    copy = COPY[locale]; root = base.rstrip('/') + '/' + PREFIX[locale]
    if state == 'pending':
        kicker, title, body = copy['pending_kicker'], copy['pending'], copy['pending_body']
        links = f'<p><a href="{escape(root + "subscribe/")}">{copy["help"]}</a></p>'
    elif state == 'confirmed':
        kicker, title, body = copy['done_kicker'], copy['done'], copy['done_body']
        links = f'<p><a class="button" href="{escape(root + "diario/")}">{copy["today"]}</a></p><p><a href="{escape(root + "archive/")}">{copy["archive"]}</a></p>'
    elif state == 'unsubscribed':
        kicker, title, body = copy['unsub_kicker'], copy['unsub'], copy['unsub_body']
        links = f'<p><a href="{escape(root + "subscribe/")}">{copy["again"]}</a></p>'
        if locale == 'en':
            links += ''.join(f'<p lang="{loc}">{COPY[loc]["unsub_body"]}</p>' for loc in ('es-419', 'zh-Hans'))
    else: raise ValueError('unknown subscription state')
    return (f'<section class="sub-state sub-state--{state}" data-state="{state}">'
            f'<p class="section-kicker">{kicker}</p><{tag} tabindex="-1">{title}</{tag}><p>{body}</p>{links}</section>')
