# Plan de difusión de 4 semanas — FCMO AI Newsletter

Estado de partida (2026-10-08): el sitio publica a diario, está en inglés, español y chino, y tiene feeds RSS, Atom y JSON. **El alta por correo aún no está activa** (la página de suscripción dice "abre en el lanzamiento"). Hasta que lo esté, el llamado a la acción es el feed y el enlace a la última edición.

## Qué se promete y qué no

Se puede decir hoy, porque cada punto se comprueba en el propio sitio:

- Cada historia muestra grado de evidencia, confianza, afirmaciones por tipo de prueba y un lugar fijo para "qué no está establecido".
- La escribe un sistema automatizado de investigación y pasa por compuertas deterministas; el sitio lo dice en cada historia.
- Las historias retiradas siguen listadas con su motivo (página de correcciones).
- Tres idiomas nativos y datos legibles por máquina.

No se dice, hasta que exista la prueba (Compuerta P de `STRATEGY-v1.md`):

- "El más auditable", "el mejor", "único", "independiente".
- Cualquier tasa de error. Se publica sólo cuando haya cuatro semanas de muestra ciega medida.
- "Verificado" como sello. La palabra correcta es "con fuente y localizador".
- Si se compara con otras publicaciones, sólo con la fórmula "entre 14 auditadas el 2026-10-04" y nombrando a la más cercana (The Governance Gazette).

## Quién publica

- **Cuenta de la publicación** (la oficial, una sola voz): LinkedIn y X. Sólo texto del kit, sin opinión personal.
- **Javier** (fCMO): LinkedIn, en primera persona, una nota breve por semana que recomienda la Newsletter con su propia razón. Es su decisión cuándo y qué escribe.
- **Matías**: círculos técnicos (X, comunidades de IA en español). Ídem.
- **WhatsApp**: sólo reenvíos a personas conocidas, uno a uno o a grupos donde ya participan. Nunca listas compradas ni altas sin permiso.

Los textos están en la página `/comparte/` de cada idioma (se regeneran a diario con la historia principal) y las tarjetas en `og/<idioma>/brand.png` y `og/<idioma>/edition-AAAA-MM-DD.png`.

## Semana 0 (antes de empezar): lo que hay que dejar listo

| Qué | Quién | Hecho cuando |
|---|---|---|
| Elegir el destino del llamado a la acción: alta por correo si ya está activa, si no el feed | Operador | La página `/suscribete/` muestra formulario real o el plan sigue con feed |
| Pegar el enlace de la última edición en LinkedIn y X (borrador, sin publicar) y comprobar que sale la tarjeta | Quien publica | Captura de la vista previa guardada |
| Elegir cómo contar visitas sin rastreo invasivo (ver Métricas) | Operador | Decisión escrita |

## Semana 1 — Círculo cercano y prueba de lo que dice

Objetivo: 20 personas conocidas lo leen de verdad y devuelven una opinión.

- Lun: Javier y Matías envían por WhatsApp el texto de WhatsApp a 10 personas cada uno (gente que decide sobre IA en su trabajo). Pregunta final: "¿qué falta o qué estorba?"
- Mié: primera publicación en LinkedIn de la cuenta de la publicación (texto LinkedIn, tarjeta de la edición del día).
- Vie: publicación en X (texto X, tarjeta de la edición).
- Todo el día, cada día: responder cada comentario y mensaje el mismo día. Anotar cada objeción en una lista.
- Cierre: lista de objeciones y de errores señalados. Cada error real se corrige en el sitio, con registro en correcciones, antes de la semana 2.

## Semana 2 — Una historia por canal, con la tarjeta de esa historia

Objetivo: probar qué formato abre el enlace.

- Lun a vie: una publicación diaria en LinkedIn o X con la historia principal del día y su tarjeta (`og/<idioma>/<id>.png`). Alternar: lunes y miércoles LinkedIn, martes y jueves X, viernes ambos con "las 3 historias de la semana".
- Un solo cambio por publicación (titular, primera línea, o con y sin tarjeta) para poder comparar.
- Javier: su nota personal en LinkedIn con el enlace a `/comparte/`.
- Matías: una respuesta útil, con enlace, en 3 hilos de IA en español donde el tema de hoy ya se esté discutiendo. Nada de spam: si el enlace no aporta, no se pone.

## Semana 3 — Otros idiomas y comunidades

Objetivo: abrir el chino y el inglés, no sólo el español.

- Inglés: publicar el texto en inglés en LinkedIn y X con la edición en `/` (inglés).
- Chino: publicar el texto en chino en una cuenta o comunidad donde ya haya presencia; si no la hay, no se abre canal nuevo: se pide a una persona de confianza que lo comparta con su propio criterio.
- Buscar 5 newsletters o blogs de IA en español y escribirles una nota personal ofreciendo el feed JSON para que lo usen como fuente (no se pide enlace de vuelta).
- Revisar la lista de objeciones de la semana 1: ¿se repiten? Si sí, cambiar el texto o el producto, no repetir la publicación.

## Semana 4 — Medir, decidir y fijar el ritmo

Objetivo: dejar un ritmo sostenible y decidir qué canales siguen.

- Lun: contar todo (ver Métricas) y escribir una página de resultados en la bóveda (`Ciencia/`), incluidos los canales que no sirvieron.
- Mié: dos o tres historias del mes con mejor respuesta, republicadas con la tarjeta y una pregunta al lector.
- Vie: decidir el ritmo fijo para el mes siguiente. Regla: si un canal dio menos de 5 clics medidos en las dos semanas de prueba, se deja o se cambia el formato; no se insiste con lo mismo.

## Ritmo estable después de la semana 4

- Cuenta de la publicación: 3 publicaciones por semana (LinkedIn lun y mié, X mar y jue).
- Resumen semanal el viernes con tres historias.
- Una persona responde en el mismo día. Sin horario prometido en público (decisión E6 del operador: no se anuncia cadencia).

## Métricas (todas son conteos; no se guardan correos ni se perfila a nadie)

| Conteo | De dónde sale | Cuándo |
|---|---|---|
| Publicaciones hechas por canal | Registro propio (una línea por publicación: fecha, canal, historia, variante) | Cada publicación |
| Impresiones, clics en enlace y reenvíos por publicación | Analítica nativa de LinkedIn y X | Cada viernes |
| Respuestas y mensajes con opinión | Conteo manual | Cada viernes |
| Altas por correo nuevas y bajas | Conteo del proveedor de correo (sólo el número) | Cada viernes, cuando el alta esté activa |
| Personas que abrieron `/comparte/` o la edición enlazada | **Hoy no existe medición** en el sitio (GitHub Pages no da visitas). Si se quiere, hay que decidir un contador sin cookies; es una decisión del operador y toca la política de privacidad | Semana 0 |
| Errores señalados por lectores y cuántos se corrigieron | Lista de objeciones y página de correcciones | Cada viernes |

Qué cuenta como éxito de las 4 semanas (se fija antes de empezar, para no ajustarlo después): 20 lectores del círculo cercano con opinión escrita; 8 publicaciones propias con clics medidos; cero afirmaciones públicas que tengan que retirarse; al menos 1 corrección real publicada a partir de un comentario de lector.

## Riesgos y cómo se evitan

- **Afirmar de más.** Todo texto sale del kit. Si un texto nuevo promete algo que no está en la lista de "se puede decir hoy", no se publica.
- **Alta por correo inexistente.** No se anuncia "suscríbete por correo" mientras la página diga que abre en el lanzamiento.
- **Edición atrasada.** Antes de publicar, abrir la edición enlazada y comprobar que es de hoy o de ayer. Si el sitio muestra aviso de retraso, ese día no se promociona.
- **Datos privados.** Nunca se publican correos de lectores ni capturas con ellos.
