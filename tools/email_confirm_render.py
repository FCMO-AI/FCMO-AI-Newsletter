#!/usr/bin/env python3
"""Render the Kit double opt-in confirmation email (EN, es-419, zh-Hans) into email/kit/confirmacion/.

Pasted into Kit's confirmation-email editor by hand. Placeholders are Kit-side values that this repo does not
resolve: {{CONFIRM_URL}} (Kit's confirmation link; rename to Kit's own tag when pasting) and {{POSTAL_ADDRESS}}
(Kit's sender address block). Nothing here sends mail or states a delivery time.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'email/kit/confirmacion'
COPY = {
 'en': dict(lang='en', subject='Confirm your subscription to the FCMO AI Newsletter',
   pre='One click confirms your address. Until then we send you no editions.', kicker='One step left',
   h='Confirm your email', p='You asked to receive the FCMO AI Newsletter. Press the button to confirm this address. Until you do, we send you no editions.',
   btn='Confirm my subscription', alt='If the button does not work, copy this link into your browser:',
   what='What you will get', what_p='One short briefing a day on what changed in AI, only when there is something verified to report. Each story separates three things: shown, claimed, not established.',
   ign='Did not ask for this? Ignore this email. Without confirmation we do not subscribe you.',
   why='You receive this because this address was entered on the FCMO AI Newsletter signup form. Kit, our email provider, stores your address and records whether you open our emails and which links you click. Every edition has a one-click unsubscribe link.',
   sender='FCMO AI · newsletter@fcmo.group · Responsible: Javier Castellanos Peña, javo@fcmo.group',
   stamps=(('Shown','Direct evidence is available.'),('Claimed','Plausible, not yet verified.'),('Not established','Unverified or unresolved.'))),
 'es-419': dict(lang='es-419', subject='Confirma tu suscripción a la Newsletter de FCMO AI',
   pre='Un clic confirma tu dirección. Hasta entonces no te enviamos ediciones.', kicker='Falta un paso',
   h='Confirma tu correo', p='Pediste recibir la Newsletter de FCMO AI. Pulsa el botón para confirmar esta dirección. Hasta que lo hagas, no te enviamos ediciones.',
   btn='Confirmar mi suscripción', alt='Si el botón no funciona, copia este enlace en tu navegador:',
   what='Qué recibirás', what_p='Un resumen breve al día de lo que cambió en IA, solo cuando haya algo verificado que contar. Cada historia separa tres cosas: demostrado, afirmado, no establecido.',
   ign='¿No lo pediste? Ignora este correo. Sin confirmación no te suscribimos.',
   why='Recibes esto porque esta dirección se escribió en el formulario de la Newsletter de FCMO AI. Kit, nuestro proveedor de correo, guarda tu dirección y registra si abres nuestros correos y en qué enlaces haces clic. Cada edición trae un enlace de baja con un clic.',
   sender='FCMO AI · newsletter@fcmo.group · Responsable: Javier Castellanos Peña, javo@fcmo.group',
   stamps=(('Demostrado','Hay evidencia directa.'),('Afirmado','Plausible, aún sin verificar.'),('No establecido','Sin verificar o sin resolver.'))),
 'zh-Hans': dict(lang='zh-Hans', subject='请确认订阅 FCMO AI Newsletter',
   pre='点击一次即可确认邮箱。在此之前我们不会发送任何一期。', kicker='还差一步',
   h='确认你的邮箱', p='你申请了 FCMO AI Newsletter。请点击按钮确认此邮箱。在你确认之前，我们不会发送任何一期。',
   btn='确认订阅', alt='如果按钮无法点击，请将此链接复制到浏览器：',
   what='你将收到什么', what_p='每天一份简报，介绍人工智能的变化，只在有已核实的内容时发送。每篇报道区分三件事：已展示、仅声称、尚未确立。',
   ign='不是你申请的？请忽略这封邮件。未经确认，我们不会为你订阅。',
   why='你收到此邮件，是因为有人在 FCMO AI Newsletter 订阅表单中填写了这个邮箱。邮件服务商 Kit 保存你的邮箱，并记录你是否打开邮件以及点击了哪些链接。每期邮件都带有一键退订链接。',
   sender='FCMO AI · newsletter@fcmo.group · 责任人：Javier Castellanos Peña，javo@fcmo.group',
   stamps=(('已展示','有直接证据。'),('仅声称','合理，但尚未核实。'),('尚未确立','未核实或未解决。'))),
}
MONO = "'Courier New',Courier,monospace"; SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
MARKS = ('background:#0a0a0a;', 'background:#f2efe8;border:1px solid #0a0a0a;background-image:linear-gradient(135deg,#0a0a0a 25%,#f2efe8 25%,#f2efe8 50%,#0a0a0a 50%,#0a0a0a 75%,#f2efe8 75%);background-size:6px 6px;', 'border:1px dashed #0a0a0a;')

def html(c):
    e = escape
    rows = ''.join(
        f'<tr><td width="28" valign="top" style="padding:0 12px 10px 0;"><div class="mk{i}" style="width:20px;height:20px;border:1px solid #0a0a0a;{m}"></div></td>'
        f'<td valign="top" class="ink-soft" style="padding:0 0 10px 0;font:13px/1.4 {SANS};color:#3a3a38;"><strong style="font:700 11px/1.4 {MONO};letter-spacing:1px;text-transform:uppercase;color:#0a0a0a;" class="ink">{e(t)}</strong><br>{e(d)}</td></tr>'
        for i, (m, (t, d)) in enumerate(zip(MARKS, c['stamps'])))
    return f'''<!doctype html>
<html lang="{c['lang']}" xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><meta name="supported-color-schemes" content="light dark"><title>{e(c['subject'])}</title>
<style>
@media (prefers-color-scheme: dark){{
 .bg{{background:#0a0a0a!important}} .sheet{{background:#161615!important}} .ink{{color:#f2efe8!important}} .ink-soft{{color:#d9d5cc!important}}
 .rule{{border-color:#2a2a28!important}} .btn{{background:#f2efe8!important}} .btn a{{color:#0a0a0a!important}} .mute{{color:#8a857c!important}} a.lnk{{color:#f2efe8!important}}
 .mk0{{background:#f2efe8!important;border-color:#f2efe8!important}} .mk1{{border-color:#f2efe8!important;background-image:linear-gradient(135deg,#f2efe8 25%,#161615 25%,#161615 50%,#f2efe8 50%,#f2efe8 75%,#161615 75%)!important}} .mk2{{border-color:#f2efe8!important}}
}}
@media (max-width:620px){{ .wrap{{width:100%!important}} .pad{{padding:24px 20px!important}} .h{{font-size:30px!important}} }}
</style></head>
<body class="bg" style="margin:0;padding:0;background:#0a0a0a;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#0a0a0a;">{e(c['pre'])}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="bg" style="background:#0a0a0a;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;">
<tr><td style="padding:0 0 16px 0;font:800 22px/1 {SANS};letter-spacing:-1px;color:#f2efe8;">FCMO AI</td></tr>
<tr><td class="sheet pad" style="background:#f2efe8;padding:36px 36px 28px 36px;">
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
 <tr><td style="padding:0 0 14px 0;font:12px/1.4 {MONO};letter-spacing:2px;text-transform:uppercase;color:#3a3a38;" class="ink-soft"><span style="display:inline-block;width:10px;height:10px;background:#f05a28;margin-right:8px;"></span>{e(c['kicker'])}</td></tr>
 <tr><td class="h ink" style="padding:0 0 14px 0;font:800 38px/1.05 {SANS};letter-spacing:-1.5px;color:#0a0a0a;">{e(c['h'])}</td></tr>
 <tr><td class="ink-soft" style="padding:0 0 24px 0;font:17px/1.5 {SANS};color:#3a3a38;">{e(c['p'])}</td></tr>
 <tr><td style="padding:0 0 18px 0;"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td class="btn" bgcolor="#0a0a0a" style="background:#0a0a0a;"><a href="{{{{CONFIRM_URL}}}}" style="display:inline-block;padding:16px 28px;font:700 13px/1 {MONO};letter-spacing:2px;text-transform:uppercase;color:#f2efe8;text-decoration:none;">{e(c['btn'])}</a></td></tr></table></td></tr>
 <tr><td class="ink-soft" style="padding:0 0 26px 0;font:13px/1.5 {SANS};color:#3a3a38;">{e(c['alt'])}<br><a class="lnk" href="{{{{CONFIRM_URL}}}}" style="color:#0a0a0a;word-break:break-all;">{{{{CONFIRM_URL}}}}</a></td></tr>
 <tr><td class="rule" style="border-top:1px solid #0a0a0a;padding:20px 0 6px 0;font:700 11px/1.4 {MONO};letter-spacing:2px;text-transform:uppercase;color:#0a0a0a;"><span class="ink">{e(c['what'])}</span></td></tr>
 <tr><td class="ink-soft" style="padding:0 0 16px 0;font:15px/1.5 {SANS};color:#3a3a38;">{e(c['what_p'])}</td></tr>
 <tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table></td></tr>
 <tr><td class="ink-soft" style="padding:10px 0 0 0;font:14px/1.5 {SANS};color:#3a3a38;">{e(c['ign'])}</td></tr>
 </table>
</td></tr>
<tr><td style="padding:20px 4px 0 4px;font:12px/1.6 {SANS};color:#8a857c;" class="mute">{e(c['why'])}<br><br>{e(c['sender'])}<br>{{{{POSTAL_ADDRESS}}}}</td></tr>
</table></td></tr></table></body></html>
'''

def text(c):
    return f"""{c['subject']}
{'=' * min(len(c['subject']), 72)}

{c['kicker'].upper()}
{c['h']}

{c['p']}

{c['btn']}:
{{{{CONFIRM_URL}}}}

{c['what']}
{c['what_p']}
""" + '\n'.join(f'  [{t}] {d}' for t, d in c['stamps']) + f"""

{c['ign']}

--
{c['why']}
{c['sender']}
{{{{POSTAL_ADDRESS}}}}
"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    keys = {'en': 'en', 'es-419': 'es', 'zh-Hans': 'zh'}
    for loc, k in keys.items():
        c = COPY[loc]
        (OUT / f'{k}.html').write_text(html(c), encoding='utf-8')
        (OUT / f'{k}.txt').write_text(text(c), encoding='utf-8')
        (OUT / f'{k}.meta.txt').write_text(f"Subject: {c['subject']}\nPreheader: {c['pre']}\n", encoding='utf-8')

if __name__ == '__main__':
    main()
