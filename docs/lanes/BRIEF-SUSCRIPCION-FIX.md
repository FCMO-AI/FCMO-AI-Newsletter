# Carril nl-suscripcion-fix — cerrar los FIX de la revisión Opus

Lee `docs/suscripcion/REVISION-OPUS.md` completo: es la lista de trabajo. Lee el Agent Hub (`runtime/FCMO_RUNTIME_V1.txt`, `disciplines/WORTHY_WORK.md` porque toca datos de personas reales y el nombre de FCMO, `policy/FCMO_ETHICAL_MORAL_CONSTITUTION_V1.md` §datos personales, `disciplines/SOFTWARE_ENGINEERING.md`). Hechos nuevos del operador (10-26): las tres opciones de Settings > Advanced > Advanced Tracking de Kit nunca se activaron; fcmo.group será el dominio oficial (Javier lo compra) y fcmogroup.com es el respaldo; el píxel de aperturas de Kit no tiene interruptor documentado.

## Haz (dueño: `docs/suscripcion/*`, `legal/AVISO-PRIVACIDAD-CORREO.md`, `site-src/assets/subscribe/subscribe.css`, `site-src/assets/js/subscribe.js`, `tools/paper/templates/subscribe.py`, `tests/test_subscribe_v2.py`, `tests/test_subscription_client.mjs`)
1. Kit (puntos 1–6 de la revisión): el dominio es una variable (`news.fcmo.group` si existe en DNS, si no `news.fcmogroup.com`), el remitente usa un buzón que existe (o el paso crea el alias primero), los pasos 4/5 dejan de contradecirse y el DNS viaja como texto, el paso 8 queda marcado BLOQUEADO por dominio, se añade el paso de diseño del correo/página de Kit como unidad pendiente, y el paso 9 tiene la condición de parada (si el píxel no se apaga, no hay COMPLIANCE_READY hasta que el aviso lo describa). Marca el paso de Advanced Tracking como hecho por el operador (10-26: nunca activadas).
2. Aviso (puntos 1–3): quita «no medimos aperturas ni clics» y la frase «solo para eso» si no es verdad; describe con verdad el píxel de aperturas y el conteo de clics de Kit; añade la sección de tecnologías de rastreo (qué, para qué, cómo bloquearlo: imágenes remotas) en ES/EN/ZH; alinea aviso corto e integral (marcadores intactos).
3. Formulario (puntos 1, 3, 4, 5): kicker en color neutro (cero naranja decorativo, Design V4.0.1), un solo «otra dirección», quita el hueco de ~100 px a 1440, prueba JS del botón de reintento y del enlace de error, y regex del `required` del input de correo. Las capturas las hace Claude fuera del sandbox: no las inventes.

## Aceptación
- `PYTHONPATH=.:tests python3 -m unittest tests.test_subscribe_v2` y `node --test tests/test_subscription_client.mjs` verdes.
- `grep -rn "no medimos" legal docs/suscripcion` vacío; `grep -n "a9340e\|F05A28" site-src/assets/subscribe/subscribe.css` sin color de texto.
- `git diff --check` limpio. Nunca `FCMO_EMAIL_ENABLED=true`, nunca llamar a Kit, nunca push.
Reporte ≤10 líneas: COMMITS, ACEPTACIÓN, NO VERIFICADO, CANON. Usa TMPDIR en /var/tmp.
