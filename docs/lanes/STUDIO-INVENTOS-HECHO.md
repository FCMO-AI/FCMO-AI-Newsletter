# Studio inventos — resultado del carril

## Antes

La primera corrida completa de este cambio ejecutó 281 pruebas: 4 fallaron y 2 dieron error. Dos comprobaciones aún esperaban que un fallo técnico terminara detenido para acción humana; las otras cuatro exposiciones derivaban de una ruta absoluta de host incluida en el brief del carril.

## Después

La corrida final ejecutó 281 pruebas: 3 fallaron, 1 dio error y 1 quedó omitida. Las cuatro fallas restantes corresponden al mismo problema de privacidad: una ruta absoluta de host en el brief versionado activa el gate y hace fallar dos flujos de publicación que lo consumen. No se modificó ese archivo porque está fuera de la propiedad del carril.

Las 45 pruebas enfocadas de publicación, reintentos, avisos y reanudación pasan. Las pruebas nuevas fallaban antes de los cambios: la racha recuperable quedaba detenida, `unknown` no esperaba 30 minutos y los avisos repetidos no tenían huella ni resolución.

## Cambios

- Los fallos recuperables usan esperas de 1, 2 y 4 minutos. Al agotarlas, la publicación pasa a `escalado`, conserva su fase y causa, muestra el siguiente intento en una hora y sigue reintentando sin pedir intervención.
- El primer avance exitoso borra la racha y el escalado. Los bloqueos que sí requieren a una persona conservan su parada manual.
- `unknown` espera más de 30 minutos. Incidentes técnicos se anotan una vez por huella en el resumen local; al cambiar la huella o resolverse, el resumen registra el cambio. No se ponen en la cola de Telegram.
- Avisos de revisión solicitada y publicación verificada conservan su ruta existente.
