# Aviso de privacidad del correo: borrador y pendientes

Borrador: `legal/AVISO-PRIVACIDAD-CORREO.md` (ES + EN + ZH). No está conectado al build ni publicado. Corrección de la revisión Opus, 2026-10-26: ahora describe aperturas, clics y registros de alojamiento; no presupone que el píxel pueda apagarse.

## En juego
Correos de personas reales (datos personales), consentimiento y nombre público de FCMO AI Newsletter → evidencia exigida: aviso veraz sobre el proveedor real, responsable confirmado, revisión jurídica y recorrido de suscripción/baja verificado → evidencia que hay: borrador y hechos del operador, sin revisión jurídica ni prueba viva → **NO-GO de activación**.
ÉTICA: material (§1 privacidad y consentimiento, §2.1 veracidad) → los suscriptores deben poder confiar en qué datos se recogen; se describe el rastreo y sus límites, sin habilitar altas ni envíos.

## Línea de consentimiento junto al formulario (propuesta pendiente de revisión)
- ES: Quiero recibir la Newsletter de FCMO AI por correo. Kit registra aperturas y clics para estadísticas de entrega e interacción. Puedes darte de baja cuando quieras. Lee el aviso de privacidad para conocer el tratamiento de tus datos y cómo limitar el rastreo.
- EN: I want to receive the FCMO AI Newsletter by email. Kit records opens and clicks for delivery and interaction statistics. You can unsubscribe anytime. Read the privacy notice for details of data processing and how to limit tracking.
- ZH: 我希望通过邮件收到 FCMO AI Newsletter。Kit 记录打开和点击事件，用于投递和互动统计。你可随时退订。请阅读隐私声明，了解数据处理方式及如何限制跟踪。

La casilla actual en `subscription_states.py` enlaza el aviso. No se cambió ese archivo fuera de propiedad. La clasificación jurídica de la medición y, si corresponde, un consentimiento separado o mecanismo de oposición siguen pendientes de revisión; esta redacción no los resuelve por sí sola.

## Responsable y marcadores literales
- El aviso corto nombra a Matías Peña Szőke. El integral lo identifica como nombre propuesto pendiente de confirmación, conservando `{{RESPONSABLE}}`, `{{DOMICILIO}}`, `{{CORREO_PRIVACIDAD}}` y `{{FECHA}}`. Se preservaron los ocho marcadores del cuerpo por idioma (la revisión contaba siete; se comprobó el original: responsable ×1, domicilio ×2, contacto ×4, fecha ×1); nadie inventó un domicilio o contacto.
- Ambos describen tratamiento fuera de México y del Espacio Económico Europeo (EEE).
- **Alineación todavía BLOQUEADA:** el aviso corto generado desde `legal/email-privacy-kit.json` exige apagar aperturas y clics. El archivo está fuera de propiedad; NEEDS.md contiene sustituciones exactas en los tres idiomas para describir el mismo tratamiento que el integral. No hay `COMPLIANCE_READY` hasta integrar y revisar ese cambio y publicar ambos avisos concordantes.

## Hechos y pendientes antes de publicar
1. **Hecho del operador, 2026-10-26:** las tres opciones de Settings > Advanced > Advanced Tracking nunca se activaron. No apagan el píxel de aperturas ni el conteo de clics. No hay interruptor documentado para el píxel. Consultar soporte y conservar la respuesta; si no se apaga, el aviso debe describirlo antes de cualquier activación.
2. Verificar doble confirmación en EN/ES/ZH. Diseño del correo/página alojada y destinos de confirmación bloqueados según `LISTA-KIT-MATIAS.md`; ninguna prueba viva hecha aquí.
3. Fijar plazo real de retención de no confirmados, supresión y eventos de apertura/clics con Kit; el borrador no inventa números. Confirmar acuerdos de encargado/transferencias (DPA) y salvaguardas fuera de México/EEE.
4. Revisión jurídica pendiente de los plazos ARCO (20 + 15 días hábiles), autoridad vigente tras la reforma de 2025 y tratamiento de medición. No se verificó legislación en este carril sin red; no es un aviso aprobado.
5. El build espera JSON por proveedor (`legal/email-privacy-kit.json`) más `FCMO_EMAIL_PRIVACY_URL`; el integral debe servirse en esa URL. No se cableó ni publicó nada. Los respaldos cifrados del repo caducan a los 30 días; confirmar operación real antes de prometerla.
