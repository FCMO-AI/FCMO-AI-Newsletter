# Lista Kit para Matías (11 pasos, cuenta Free)

Entra a kit.com con la cuenta de la Newsletter. No hace falta pagar nada.

1. **Dirección postal.** Abajo a la izquierda: Settings > Email > Mailing Address. Pon la dirección postal que tú elijas (la misma que irá al secret `FCMO_EMAIL_POSTAL_ADDRESS`). Guarda.
2. **Remitente.** En esa misma página, From: nombre `FCMO AI`, correo `hola@news.fcmogroup.com` (o el que acuerdes). Confirma el correo que Kit te mande.
3. **Dominio verificado.** Settings > Email > Verified Sending Domains > «Set up your Verified Sending Domain». Escribe `news.fcmogroup.com` > Next. **Si te pide pago o no aparece, para aquí y avísame** (plan alterno: Brevo Free).
4. **Elige «manual».** No uses «Set this up for me». Kit mostrará registros CNAME (DKIM) y un TXT; no los copies a mano, abre «Show DNS records».
5. **Pásale los registros a Javier.** Copia el bloque de `BLOQUE-JAVIER-DNS.md` en su Claude y mándale una captura de esos registros. Tipo, host y valor: tal cual los muestra Kit.
6. **Validar.** Cuando Javier diga «listo», haz clic en Validate. Si falla, espera hasta 48 h y repite. No pongas un DMARC propio antes de que Kit valide.
7. **Formularios (3 veces: EN, ES, ZH).** Abre cada formulario > Settings > Confirmation Email: «Send confirmation email» marcado; «Auto-confirm new subscribers» **desmarcado**.
8. **Después de confirmar.** En los mismos formularios, «After confirming redirect to» > URL: la página de confirmación de FCMO AI de ese idioma (te la paso). Pulsa Edit Email Contents, revisa que el texto diga qué es y cómo darse de baja; Save; Publish.
9. **Tracking.** Settings > Advanced > Advanced Tracking: apaga las tres opciones (subscriber_id, UTM, correo hasheado). Anota que el píxel de aperturas no se puede apagar según la ayuda.
10. **Prueba sin riesgo.** Con un correo tuyo propio (no de lectores), suscríbete a un formulario, comprueba que llega el correo de confirmación desde `news.fcmogroup.com`, haz clic y mira que cae en la página de redirección. Luego date de baja. No envíes ningún broadcast.
11. **Dime qué viste.** Mándame captura de «Verified» y del remitente del correo de prueba (sin mostrar claves).

Nunca me pegues la API key ni contraseñas: esa llave va sólo como secret `KIT_API_KEY` del repositorio.
