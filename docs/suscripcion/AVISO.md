# Aviso de privacidad del correo: borrador y pendientes

Borrador: `legal/AVISO-PRIVACIDAD-CORREO.md` (ES + EN + ZH). No está conectado al build ni publicado.

## En juego
Correos de personas reales (datos personales bajo LFPDPPP), consentimiento y el nombre público de FCMO AI Newsletter. Un aviso incompleto o inexacto expone al responsable a sanciones y a perder la confianza de quien se suscribe.
Evidencia exigida: aviso completo con hechos verificados del proveedor real y datos reales del responsable. Evidencia que hay: borrador redactado desde los documentos del repo; sin los tres datos de Matías y sin revisión jurídica no es publicable.
Ética: material (datos de personas a un proveedor; confianza del lector) -> el borrador no promete nada que no se pueda cumplir, no inventa responsable ni domicilio, y declara que no hay finalidades secundarias ni medición de aperturas.

## Línea de consentimiento junto al formulario
- ES: Quiero recibir la Newsletter de FCMO AI por correo. Usaremos tu correo solo para eso; puedes darte de baja cuando quieras. Lee el aviso de privacidad.
- EN: I want to receive the FCMO AI Newsletter by email. We use your email only for that; you can unsubscribe anytime. Read the privacy notice.
- ZH: 我希望通过邮件收到 FCMO AI Newsletter。我们仅将你的邮箱用于此目的，你可随时退订。请阅读隐私声明。

(La casilla actual de `subscription_states.py` dice «he leído el aviso de privacidad»: compatible; esta línea es la propuesta más explícita. No se cambió código.)

## Pendientes de Matías (marcadores literales)
- `{{RESPONSABLE}}`, `{{DOMICILIO}}`, `{{CORREO_PRIVACIDAD}}`. Además `{{FECHA}}`, que se fija al publicar.

## Hechos a verificar antes de publicar (no los afirmé como comprobados)
1. Kit: que open/click tracking esté apagado en la cuenta (el aviso dice que no medimos aperturas). Que la doble confirmación esté activa en los 3 formularios.
2. Kit: plazo real de retención de no confirmados y de supresión (el aviso remite a la configuración; conviene fijar un número).
3. Plazos ARCO (20 + 15 días hábiles) y nombre de la autoridad vigente tras la reforma LFPDPPP de 2025: revisar con abogado. Dejé la autoridad sin nombre a propósito.
4. Si se quiere citar el acuerdo de encargado/transferencias con Kit (DPA).
5. Cómo se publicará: el build espera JSON por proveedor (`legal/email-privacy-kit.json`) más `FCMO_EMAIL_PRIVACY_URL`; el aviso integral debe servirse en esa URL. No se cableó nada.
