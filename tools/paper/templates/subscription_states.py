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
        'help': 'Not there yet? Look in spam or promotions, then try another address.',
        'done_kicker': 'Confirmed', 'done': 'You’re subscribed', 'done_body': 'After email confirmation, the next fresh edition will arrive in your inbox. Until then, today’s is here.',
        'today': 'Read today’s edition', 'archive': 'Browse the archive',
        'unsub_kicker': 'Unsubscribed', 'unsub': 'You’re unsubscribed',
        'unsub_body': 'After the provider confirms your unsubscribe request, no further editions will be sent. The newspaper remains free to read.',
        'notice_h': 'Before you subscribe',
        'notice': ('We keep your email address, your edition language and your consent. Kit, our email provider, stores them and may process them outside Mexico.',
                   'Kit records whether you open our emails and which links you click.',
                   'Every email has a one-click unsubscribe link. Responsible: Javier Castellanos Peña, javo@fcmo.group.'),
        'steps': ('Open the email from FCMO AI, sent by newsletter@fcmo.group.', 'Press the confirm button inside it.', 'Until you do, we send you no editions.'),
        'stamp_pending': ('Not established', 'Your address is not confirmed yet. Only the button in the email confirms it.'),
        'stamp_done': ('Claimed', 'Kit sent you here. This page is a notice, not a receipt: Kit keeps the record.'),
        'stamp_unsub': ('Claimed', 'Kit sent you here. This page is a notice, not a receipt: Kit keeps the record.'),
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
        'help': '¿Aún no llega? Mira en spam o promociones y prueba con otra dirección.',
        'done_kicker': 'Confirmado', 'done': 'Ya estás suscrito', 'done_body': 'Después de confirmar tu correo, la próxima edición con novedades llegará a tu bandeja. Mientras tanto, la de hoy está aquí.',
        'today': 'Leer la edición de hoy', 'archive': 'Ver el archivo',
        'unsub_kicker': 'Baja confirmada', 'unsub': 'Ya estás dado de baja',
        'unsub_body': 'Después de que el proveedor confirme tu baja, no recibirás más ediciones. El periódico sigue disponible gratis.',
        'notice_h': 'Antes de suscribirte',
        'notice': ('Guardamos tu correo, el idioma de la edición y tu consentimiento. Kit, nuestro proveedor de correo, los almacena y puede tratarlos fuera de México.',
                   'Kit registra si abres nuestros correos y en qué enlaces haces clic.',
                   'Cada correo trae un enlace de baja con un clic. Responsable: Javier Castellanos Peña, javo@fcmo.group.'),
        'steps': ('Abre el correo de FCMO AI, enviado desde newsletter@fcmo.group.', 'Pulsa el botón de confirmar que trae.', 'Hasta que lo hagas, no te enviamos ediciones.'),
        'stamp_pending': ('No establecido', 'Tu dirección aún no está confirmada. Solo el botón del correo la confirma.'),
        'stamp_done': ('Afirmado', 'Kit te envió aquí. Esta página es un aviso, no un comprobante: Kit conserva el registro.'),
        'stamp_unsub': ('Afirmado', 'Kit te envió aquí. Esta página es un aviso, no un comprobante: Kit conserva el registro.'),
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
        'help': '还没收到？请查看垃圾邮件或促销邮件，或换一个邮箱。',
        'done_kicker': '已确认', 'done': '订阅成功', 'done_body': '确认邮箱后，下一期有新内容的简报将发送到你的邮箱。在此之前，可以先读今天这一期。',
        'today': '阅读今天这一期', 'archive': '浏览往期',
        'unsub_kicker': '已退订', 'unsub': '你已退订',
        'notice_h': '订阅之前',
        'notice': ('我们保存你的邮箱地址、版本语言和同意记录。邮件服务商 Kit 负责存储，并可能在墨西哥境外处理。',
                   'Kit 会记录你是否打开邮件以及点击了哪些链接。',
                   '每封邮件都带有一键退订链接。责任人：Javier Castellanos Peña，javo@fcmo.group。'),
        'steps': ('打开 FCMO AI 的邮件，发件地址 newsletter@fcmo.group。', '点击邮件中的确认按钮。', '在你确认之前，我们不会发送任何一期。'),
        'stamp_pending': ('尚未确立', '你的邮箱尚未确认。只有邮件中的按钮才算确认。'),
        'stamp_done': ('仅声称', '这是 Kit 把你送到此页。本页只是提示，不是回执：记录由 Kit 保存。'),
        'stamp_unsub': ('仅声称', '这是 Kit 把你送到此页。本页只是提示，不是回执：记录由 Kit 保存。'),
        'unsub_body': '服务商确认退订后，你将不再收到后续邮件。你仍可免费阅读报纸。', 'again': '重新订阅',
    },
}

MARK = {'pending': 'gap', 'confirmed': 'claimed', 'unsubscribed': 'claimed'}
STAMP = {'pending': 'stamp_pending', 'confirmed': 'stamp_done', 'unsubscribed': 'stamp_unsub'}


def state_page(locale, state, base, *, tag='h1'):
    copy = COPY[locale]; root = base.rstrip('/') + '/' + PREFIX[locale]
    if state == 'pending':
        kicker, title, body = copy['pending_kicker'], copy['pending'], copy['pending_body']
        links = ''
    elif state == 'confirmed':
        kicker, title, body = copy['done_kicker'], copy['done'], copy['done_body']
        links = f'<p><a class="button" href="{escape(root)}">{copy["today"]}</a></p><p><a href="{escape(root + "archive/")}">{copy["archive"]}</a></p>'
    elif state == 'unsubscribed':
        kicker, title, body = copy['unsub_kicker'], copy['unsub'], copy['unsub_body']
        links = f'<p><a href="{escape(root + "subscribe/")}">{copy["again"]}</a></p>'
        if locale == 'en':
            links += ''.join(f'<p lang="{loc}">{COPY[loc]["unsub_body"]}</p>' for loc in ('es-419', 'zh-Hans'))
    else: raise ValueError('unknown subscription state')
    label, note = copy[STAMP[state]]
    stamp = (f'<div class="sub-stamp"><span class="sub-mark sub-mark-{MARK[state]}" aria-hidden="true"></span>'
             f'<div><strong>{escape(label)}</strong><span>{escape(note)}</span></div></div>')
    sheet_body = ''
    if state == 'pending':
        sheet_body = ('<ol class="sub-steps">' + ''.join(f'<li><span>{escape(t)}</span></li>' for t in copy['steps']) + '</ol>'
                      f'<p class="sub-fine">{escape(copy["help"])}</p>')
    sheet = f'<div class="sub-sheet">{stamp}{sheet_body}</div>'
    return (f'<section class="sub-state sub-state--{state}" data-state="{state}">'
            f'<p class="section-kicker">{kicker}</p><{tag} tabindex="-1">{title}</{tag}><p>{body}</p>{links}{sheet}</section>')
