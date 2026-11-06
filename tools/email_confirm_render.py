#!/usr/bin/env python3
"""Render Kit HTML templates and incentive-email copy (EN, es-419, zh-Hans).

Kit owns the confirmation button in the incentive email. The HTML template uses Kit's documented
message_content, unsubscribe_url and address variables; no confirmation URL is invented here.
Nothing here sends mail or states a delivery time.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'email/kit'
COPY = {
 'en': dict(lang='en', subject='Confirm your subscription to the FCMO AI Newsletter', copy_label='Body text for Kit:', kicker='One step left',
   h='Confirm your email', p='You asked to receive the FCMO AI Newsletter. Press the button to confirm this address. Until you do, we send you no editions.',
   btn='Confirm my subscription', unsubscribe='Unsubscribe', setup='Suggested subject: “{subject}”. Kit setup: use Kit’s built-in confirmation button and set its label to “{button}”. Do not paste this note; paste only the body below into the incentive email editor.',
   what='What you will get', what_p='One short briefing a day on what changed in AI, only when there is something verified to report. Each story separates three things: shown, claimed, not established.',
   ign='Did not ask for this? Ignore this email. Without confirmation we do not subscribe you.',
   why='You receive this because this address was entered on the FCMO AI Newsletter signup form. Kit, our email provider, stores your address and records whether you open our emails and which links you click. Every edition has a one-click unsubscribe link.',
   sender='FCMO AI · newsletter@fcmo.group · Responsible: Javier Castellanos Peña, javo@fcmo.group',
   stamps=(('Shown','Direct evidence is available.'),('Claimed','Plausible, not yet verified.'),('Not established','Unverified or unresolved.'))),
 'es-419': dict(lang='es-419', subject='Confirma tu suscripción a la Newsletter de FCMO AI', copy_label='Texto para el cuerpo:', kicker='Falta un paso',
   h='Confirma tu correo', p='Pediste recibir la Newsletter de FCMO AI. Pulsa el botón para confirmar esta dirección. Hasta que lo hagas, no te enviamos ediciones.',
   btn='Confirmar mi suscripción', unsubscribe='Cancelar suscripción', setup='Asunto sugerido: «{subject}». Configuración de Kit: usa el botón de confirmación integrado de Kit y ponle el texto «{button}». No pegues esta nota; pega solo el cuerpo de abajo en el editor del correo de incentivo.',
   what='Qué recibirás', what_p='Un resumen breve al día de lo que cambió en IA, solo cuando haya algo verificado que contar. Cada historia separa tres cosas: demostrado, afirmado, no establecido.',
   ign='¿No lo pediste? Ignora este correo. Sin confirmación no te suscribimos.',
   why='Recibes esto porque esta dirección se escribió en el formulario de la Newsletter de FCMO AI. Kit, nuestro proveedor de correo, guarda tu dirección y registra si abres nuestros correos y en qué enlaces haces clic. Cada edición trae un enlace de baja con un clic.',
   sender='FCMO AI · newsletter@fcmo.group · Responsable: Javier Castellanos Peña, javo@fcmo.group',
   stamps=(('Demostrado','Hay evidencia directa.'),('Afirmado','Plausible, aún sin verificar.'),('No establecido','Sin verificar o sin resolver.'))),
 'zh-Hans': dict(lang='zh-Hans', subject='请确认订阅 FCMO AI Newsletter', copy_label='正文：', kicker='还差一步',
   h='确认你的邮箱', p='你申请了 FCMO AI Newsletter。请点击按钮确认此邮箱。在你确认之前，我们不会发送任何一期。',
   btn='确认订阅', unsubscribe='取消订阅', setup='建议主题：{subject}。Kit 设置：使用 Kit 自带的确认按钮，并将按钮文字设为“{button}”。不要粘贴这段说明；只把下面的正文粘贴到激励邮件编辑器中。',
   what='你将收到什么', what_p='每天一份简报，介绍人工智能的变化，只在有已核实的内容时发送。每篇报道区分三件事：已展示、仅声称、尚未确立。',
   ign='不是你申请的？请忽略这封邮件。未经确认，我们不会为你订阅。',
   why='你收到此邮件，是因为有人在 FCMO AI Newsletter 订阅表单中填写了这个邮箱。邮件服务商 Kit 保存你的邮箱，并记录你是否打开邮件以及点击了哪些链接。每期邮件都带有一键退订链接。',
   sender='FCMO AI · newsletter@fcmo.group · 责任人：Javier Castellanos Peña，javo@fcmo.group',
   stamps=(('已展示','有直接证据。'),('仅声称','合理，但尚未核实。'),('尚未确立','未核实或未解决。'))),
}
MONO = "'Courier New',Courier,monospace"; SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
# The site's stepped mark, drawn with table cells so it needs no hosted image and survives image blocking.
def _bm(w, h): return f'<td class="bm" width="{w}" height="{h}" bgcolor="#0a0a0a" style="background:#0a0a0a;font-size:0;line-height:0;width:{w}px;height:{h}px;">&nbsp;</td>'
def _sp(w, h): return f'<td width="{w}" height="{h}" style="font-size:0;line-height:0;width:{w}px;height:{h}px;">&nbsp;</td>'
BRAND = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
         '<td valign="middle" style="padding:0 10px 0 0;"><table role="presentation" cellpadding="0" cellspacing="0" border="0" width="28">'
         f'<tr>{_sp(16, 11)}{_bm(12, 11)}</tr><tr>{_sp(28, 3)}</tr>'
         f'<tr><td colspan="2" style="padding:0;"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>{_sp(6, 8)}{_bm(8, 8)}</tr></table></td></tr>'
         f'<tr><td colspan="2" style="padding:0;"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>{_sp(1, 6)}{_bm(5, 6)}</tr></table></td></tr></table></td>'
         f'<td valign="middle" class="brand" style="font:800 24px/1 {SANS};letter-spacing:-1px;color:#0a0a0a;">FCMO AI</td></tr></table>')
def html(c):
    e = escape
    brand = BRAND
    return f'''<!doctype html>
<html lang="{c['lang']}" xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><meta name="supported-color-schemes" content="light dark"><title>{e(c['subject'])}</title>
<style>
@media (prefers-color-scheme: dark){{
 .bg{{background:#0a0a0a!important}} .sheet{{background:#161615!important;border-color:#2a2a28!important}} .ink-soft{{color:#d9d5cc!important}}
 .mute{{color:#b5b0a6!important}} .brand{{color:#f2efe8!important}} .bm{{background:#f2efe8!important}}
}}
@media (max-width:620px){{ .wrap{{width:100%!important}} .pad{{padding:24px 20px!important}} }}
</style></head>
<body class="bg" style="margin:0;padding:0;background:#e3dfd5;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="bg" style="background:#e3dfd5;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;">
<tr><td style="padding:0 0 16px 0;">{brand}</td></tr>
<tr><td class="sheet pad" style="background:#f2efe8;border:1px solid #0a0a0a;padding:36px 36px 28px 36px;">
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
 <tr><td class="ink-soft" style="font:15px/1.55 {SANS};color:#3a3a38;">{{{{ message_content }}}}</td></tr>
 </table>
</td></tr>
<tr><td style="padding:20px 4px 0 4px;font:12px/1.6 {SANS};color:#4a4741;" class="mute">{e(c['why'])}<br><br>{e(c['sender'])}<br>{{{{ address }}}}<br><br><a href="{{{{ unsubscribe_url }}}}" style="color:#4a4741;">{e(c['unsubscribe'])}</a></td></tr>
</table></td></tr></table></body></html>
'''

def incentive(c):
    return f"""{c['setup'].format(button=c['btn'], subject=c['subject'])}

{c['copy_label']}

{c['kicker'].upper()}
{c['h']}

{c['p']}

{c['what']}
{c['what_p']}
""" + '\n'.join(f'[{t}] {d}' for t, d in c['stamps']) + f"""

{c['ign']}
"""

def main():
    (OUT / 'plantilla').mkdir(parents=True, exist_ok=True)
    (OUT / 'incentivo').mkdir(parents=True, exist_ok=True)
    keys = {'en': 'en', 'es-419': 'es', 'zh-Hans': 'zh'}
    for loc, k in keys.items():
        c = COPY[loc]
        (OUT / f'plantilla/{k}.html').write_text(html(c), encoding='utf-8')
        (OUT / f'incentivo/{k}.md').write_text(incentive(c), encoding='utf-8')

if __name__ == '__main__':
    main()
