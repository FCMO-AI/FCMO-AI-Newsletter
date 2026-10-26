# Kit plan Free (Newsletter): qué permite, para la suscripción de FCMO AI

Investigado 2026-10-26 (solo lectura web, sin tocar la cuenta). Cada dato lleva su fuente. Lo que Kit **no documenta** está marcado «NO CONFIRMADO»: se verifica en la UI antes de activar.

**En juego:** correos a personas reales con su dirección, bajo el nombre público de FCMO AI (reputación del dominio, consentimiento, aviso de privacidad). **Evidencia exigida:** dominio autenticado, DOI funcionando, dirección postal y baja verificados con una cuenta semilla. **Evidencia que hay:** documentación oficial de Kit (abajo) y, en el repo, un probe del operador del 2026-10-05; falta la prueba viva en la cuenta.

## Resumen
| Pregunta | Respuesta |
|---|---|
| 1. Dominio propio autenticado en Free | Kit lo documenta sin atarlo a un plan; reseñas de terceros dicen que Free lo incluye. **NO CONFIRMADO oficialmente**: se ve en Settings > Email > Verified Sending Domains con la cuenta Free. Subdominio permitido. |
| 2. Dirección postal | Settings > Email > Mailing Address |
| 3. Doble opt-in | Por formulario: Settings > Confirmation Email. Dejar «Auto-confirm» sin marcar |
| 4. Apagar tracking de aperturas/clics | **No hay interruptor documentado.** Sólo se apagan los parámetros de enlace (Settings > Advanced) |
| 5. Límites Free | 10 000 suscriptores, broadcasts/formularios ilimitados, API sí; sin secuencias ni automatizaciones |

## 1. Dominio de envío verificado (DKIM/SPF/DMARC)
- Ruta: **Settings** (abajo a la izquierda) > **Email** > **Verified Sending Domains** > «Set up your Verified Sending Domain», escribir el dominio, *Next*; «Set this up for me» (Entri, automático) o manual; luego **Validate**. [Verify your domain](https://help.kit.com/en/articles/2502558-verify-your-domain-to-optimize-your-deliverability)
- Acepta dominio raíz **y subdominios** (mismo artículo). Sirve `news.fcmogroup.com`.
- Registros: Kit los genera y los muestra en esa pantalla («Show DNS records» junto al dominio). El artículo habla de proceso manual con **CNAME** (ejemplos de host truncado `ckespa` y `cka._domainkey`) y de un **TXT de DMARC** que empieza con `p=none`. [DMARC en dominio verificado](https://help.kit.com/en/articles/8540237-how-to-add-a-dmarc-record-to-your-verified-sending-domain). Los valores exactos sólo aparecen en la UI: no se pueden inventar ni copiar de otra cuenta. Terceros dicen SPF = TXT y DKIM = CNAME ([EasyDMARC](https://easydmarc.com/blog/convertkit-spf-and-dkim-configuration/), no oficial).
- Avisos de Kit: algunos DNS (p. ej. Bluehost) rechazan puntos en el host, usar el nombre truncado; propagación de 24 a 48 h; no borrar el DMARC después; las aperturas pueden bajar 2 a 3 semanas mientras se recalcula la reputación. [Antes de verificar](https://help.kit.com/en/articles/9176509-what-you-should-know-before-setting-up-a-verified-sending-domain)
- Sin verificar, Kit firma con su dominio compartido y un DMARC propio sin verificar manda al spam ([unspam.email](https://unspam.email/deliverability/kit), tercero): **no publicar DMARC estricto antes de validar en Kit.**
- Plan: ni «The Kit Free plan» ([ayuda](https://help.kit.com/en/articles/16627071-the-kit-free-plan)) ni los artículos de dominio dicen que sea de pago ni que esté incluido. Terceros ([EmailToolTester](https://www.emailtooltester.com/en/reviews/convertkit/) y otras) dicen que Free lo incluye. La comparación Creator/Pro lista «custom domains», que es otra cosa (URL de páginas, [ayuda](https://help.kit.com/en/articles/8492610-how-to-set-up-a-custom-domain-in-kit)). La página de precios devolvió 429 y no se pudo leer.
- **Si Free no lo permitiera:** Creator desde **USD 39/mes** (33 anual) hasta 1 000 suscriptores; Pro desde 79 ([comparación](https://help.kit.com/en/articles/4494683-creator-plan-vs-creator-pro-plan)). Brevo Free (300 correos/día, contactos ilimitados) sí autentica dominio propio sin pagar (Senders & IP > Domains; DKIM obligatorio desde feb 2024) pero deja su logo en el pie ([guía](https://unspam.email/deliverability/brevo), tercero). Nota: 300/día con tres listas cuenta por lista (ver `docs/EMAIL-PROVIDERS.md`). Kit Free cuesta 0 y no tiene tope diario documentado; si el dominio se confirma, Kit gana; si no, Brevo Free antes que pagar 39.

## 2. Dirección postal
**Settings > Email > sección Mailing Address**; alimenta `{{ address }}` en plantillas. Todo correo, incluido el de confirmación, la necesita. Kit ofrece su propia dirección (Seattle) sólo para correo vía Kit. [Alternativas](https://help.kit.com/en/articles/2502494-alternatives-for-your-physical-address). Debe coincidir con el secret `FCMO_EMAIL_POSTAL_ADDRESS` del repo; la dirección la decide el operador.

## 3. Doble opt-in y redirección
Por formulario: abrir el formulario > **Settings** > pestaña **Confirmation Email**. [La confirmación](https://help.kit.com/en/articles/2502655-the-confirmation-email)
- **Send confirmation email**: marcado (desmarcarlo apaga el DOI).
- **Auto-confirm new subscribers**: **sin marcar** (marcado confirma sin clic; es lo que Kit llama saltarse el DOI).
- **After confirming redirect to** > URL: página propia de «suscripción confirmada». Por defecto va a una página de Kit no editable.
- **Edit Email Contents**: remitente, asunto (sin personalización), cuerpo; es el «incentive email». Guardar, guardar el formulario y **Publish**. Hacerlo en los 3 formularios (EN/ES/ZH).

## 4. Tracking
- La apertura se mide con un píxel de 1 px en el pie ([cómo funciona](https://help.kit.com/en/articles/2502687-how-email-open-tracking-works)); la documentación no ofrece apagarlo ni apagar el conteo de clics. **NO CONFIRMADO**: preguntar a soporte de Kit si hay interruptor.
- Sí se apagan: Settings > **Advanced** > Advanced Tracking: `subscriber_id`, UTM automáticos y correo hasheado en enlaces. [Global advanced tracking](https://help.kit.com/en/articles/9375532-global-advanced-tracking). Apagar los tres.
- Consecuencia ética: si el aviso de privacidad dice «sin seguimiento», Kit lo contradice mientras el píxel exista. El aviso debe decir lo que Kit hace.

## 5. Límites Free
Hasta 10 000 suscriptores; formularios, landings y broadcasts ilimitados; etiquetas y segmentos; A/B en broadcasts; **API**. Sin automatizaciones visuales, secuencias, reglas/RSS, AI Connectors. Soporte en 24 h. [Free plan](https://help.kit.com/en/articles/16627071-the-kit-free-plan). Un artículo antiguo habla de 1 automatización básica; el actual manda. Pasado 10 000 hay que subir de plan. El probe del 2026-10-05 del repo ya vio 422 en filtros por formulario en Free.

## Ética
Material: direcciones y consentimiento de personas reales y el nombre público de FCMO. Mitigación: DOI real, sin auto-confirm, dirección postal, aviso que describa el píxel, nadie suscrito ni enviado en esta fase.
