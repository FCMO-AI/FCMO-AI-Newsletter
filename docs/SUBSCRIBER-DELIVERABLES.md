# Qué recibe el suscriptor

Propuesta de producto para FCMO AI Newsletter. «Preparado» describe código disponible,
no confirma activación del proveedor ni recepción en una bandeja real.

| Entregable | Web | Correo | RSS, Atom y JSON Feed | Estado y siguiente paso |
| --- | --- | --- | --- | --- |
| Edición diaria | Diario y archivo por idioma | Resumen con evidencia y enlaces, en el idioma elegido | Feeds por idioma | Preparado. Solo enviar novedades frescas de una publicación verificada; no llenar días sin novedades. |
| Ensayos, cartas y notas de autor | Texto completo, fuentes, figuras y correcciones | Pieza completa adaptada al correo; el autor elige si enviarla | Feeds de piezas por idioma | Preparado. Se programa después de verificar la web, una vez por pieza e idioma. Una corrección no provoca reenvío automático. |
| Resumen semanal | Página fechada con las decisiones y cambios de la semana | Un resumen compacto, con enlaces a las piezas completas | Una entrada semanal | Propuesto. Faltan selección editorial, plantilla, archivo, preferencias e idempotencia propios. |
| Alertas relevantes | Nota breve con evidencia, fecha y vínculo estable | Mensaje excepcional para lectores que lo pidan | Entrada con categoría de alerta | Propuesto. Faltan criterios de relevancia, consentimiento separado, límites de frecuencia y comprobación de correcciones. |
| Avisos de corrección o retiro | Historial y motivo en la pieza | Aviso separado para cambios materiales, con vínculo al historial | Entrada de corrección con identidad propia | La web existe; el aviso dedicado está pendiente. Definir cuándo avisar y evitar duplicados. |

El alta diaria usa un formulario por idioma: inglés, español latinoamericano o chino
simplificado. La confirmación y la baja pertenecen al proveedor de correo. Antes de
confirmar no se envían ediciones; los estados cancelado, rebote y queja quedan
excluidos. La web no guarda direcciones ni tokens. Los feeds se pueden seguir sin
entregar una dirección.

La elección de idioma se expresa hoy con el formulario correspondiente. Kit permite
membresías en varios formularios; eso puede producir varias ediciones para una misma
persona. Un centro de preferencias que cambie a un solo idioma y permita elegir
diario, piezas, resumen semanal y alertas sigue pendiente. No interpretar un alta en
otro formulario como autorización para quitar una suscripción existente.

La experiencia preparada incluye `/subscribe/`, `/subscribe/check-inbox/`,
`/subscribed/` y `/unsubscribed/`, con sus equivalentes `/es/` y `/zh/`. Las páginas
de retorno son presentación, no recibos de estado. Una respuesta opaca al enviar el
formulario deja al lector pendiente de confirmación. «Programado» en Studio significa
que el proveedor confirmó la programación; no demuestra entrega, apertura ni lectura.

Antes de activar promesas de correo, configurar doble opt-in, remitente, aviso
integral, dirección postal y las redirecciones de confirmación y baja; comprobarlas
con buzones de prueba fuera de las pruebas automatizadas. Usar la próxima edición
como promesa de llegada, sin prometer una hora ni un día que aún no se verificó.
