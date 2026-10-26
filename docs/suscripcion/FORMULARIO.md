# Formulario de suscripción (Kit, EN/ES/ZH)

**En juego:** datos personales, consentimiento y nombre público de FCMO AI → **evidencia exigida:** formulario accesible y estados honestos, diseño juzgado en navegador y doble opt-in/baja probados con cuenta semilla → **evidencia que hay:** pruebas de HTML y JS local con transporte simulado; capturas de la versión anterior → **NO-GO de activación**.
**ÉTICA: material (§1 y §2.1)** → consentimiento obligatorio desmarcado y estado pendiente condicional; una respuesta opaca no prueba recepción ni suscripción.

## Correcciones del carril nl-suscripcion-fix
- Kicker en color neutro. El cuadro de 10 px sigue siendo el acento existente; no se añade naranja al texto.
- Un solo control en pendiente: la ayuda de spam/promociones y cambio de dirección ahora es el botón de reintento. Se conservan las cadenas de ES/EN/ZH de la presentación existente. No hay un enlace duplicado de navegación.
- En escritorio, título/lede y lista comparten una columna independiente del panel de formulario, con separación de 1 rem; la altura del panel ya no reparte espacio entre esos bloques. El canal horizontal conserva su valor. Se elimina también el margen inferior del lede que se sumaba al hueco. La regla móvil conserva una columna, formulario antes de la lista y separación de 2 rem.
- Pruebas JS del reintento: regresa a idle, oculta pendiente, libera la altura reservada, enfoca y selecciona el correo sin borrarlo, y permite volver a enviar. Pruebas del enlace de error: oculto inicialmente, visible tras fallo, mismo destino alojado y oculto al reintentar. El JS de producción ya hacía esto; no requirió modificación.
- La aserción de `required` ahora coincide con la etiqueta del propio input de correo, sin poder satisfacerse con el checkbox.
- La bandera de correo no se habilitó. El test de bandera apagada sigue comprobando «próximamente» sin formulario. No hubo POST a Kit.

## Capturas y revisión pendientes (Claude fuera del sandbox)
Las imágenes de `capturas/` pertenecen a la versión anterior; no prueban estas correcciones. Este carril no generó ni alteró capturas. La corrección CSS tiene prueba de estructura, **no una medida visual de píxeles**.

Batería pendiente: abrir EN/ES/ZH a 1440, 390 y 320 px; revisar idle, enviando, pendiente, reintento, error con enlace alojado completo (hacer scroll y comprobar que la barra inferior no lo tape), noscript y bandera apagada. En 1440 comprobar distancia lede/lista y espacio inferior; en móvil comprobar orden y foco. Anotar resultado de cada caso y capturas del candidato. Matías debe juzgar el híbrido claro/oscuro frente a R4 antes de llamarlo visualmente terminado.

La página alojada y el correo de confirmación stock de Kit siguen rechazados; su diseño es una unidad pendiente en `LISTA-KIT-MATIAS.md`. El enlace de error y noscript conservan su función, pero no se pueden dar por visualmente aprobados hasta cerrar esa unidad. Sigue pendiente el choque de los enlaces «Correcciones»/«Suscribirme» de la barra inferior a 320 px, fuera de propiedad.

## Pruebas reproducibles
- `TMPDIR=/var/tmp PYTHONPATH=.:tests python3 -m unittest tests.test_subscribe_v2`
- `TMPDIR=/var/tmp node --test tests/test_subscription_client.mjs`

La revisión Opus informó una suite completa anterior de 1274 pruebas (9 omitidas); no se atribuye esa corrida al candidato de este carril.
