# Para Javier: pégale esto a tu Claude

Matías completa las dos variables con la elección del paso 0 de `LISTA-KIT-MATIAS.md` y adjunta los registros **como texto**. `fcmo.group` será el oficial (Javier lo compra): usa `news.fcmo.group` cuando esté comprado y disponible en DNS. FCMO no tiene otro dominio (Matías, 10-26: fcmogroup.com y fcmo.ai no son de FCMO); sin fcmo.group comprado, este paso está BLOQUEADO. No se ha comprobado DNS desde este carril.

Copia todo lo que está entre las líneas y pégalo en tu Claude.

---
Soy Javier y administro el DNS en GoDaddy. Necesito autenticar un subdominio para enviar correo de la Newsletter de FCMO AI con Kit (kit.com). Ayúdame paso a paso, una cosa a la vez y en español sencillo.

Elección que Matías debe completar antes de empezar:
- DOMINIO_RAIZ = fcmo.group (sólo cuando esté comprado; no hay respaldo)
- DOMINIO_ENVIO = [news. seguido del DOMINIO_RAIZ elegido]

Reglas:
- Si las variables no están resueltas, pide la elección; nunca supongas que el dominio ya está comprado ni lo compres tú.
- En GoDaddy veré el dominio elegido > DNS > Administrar DNS y la tabla de registros (tipo, nombre, datos/valor y TTL). Dime qué botón pulsar; yo entro y hago los cambios.
- Matías pasará desde Kit (Settings > Email > Verified Sending Domains > «Show DNS records») el tipo, host/nombre y valor/destino completos de cada registro como texto. Tómalos literalmente del portapapeles, no de una captura; no inventes ni adaptes valores de otra cuenta. Si falta un valor, pídelo. Pueden ser CNAME de DKIM y TXT de DMARC, pero manda lo que Kit entregue.
- No me pidas ni pegues contraseñas, claves de API ni códigos de acceso.
- Antes de crear algo, comprueba si ya hay un registro con ese nombre y detente ante cualquier conflicto. Solo se agregan registros nuevos del subdominio DOMINIO_ENVIO; no toques el correo normal ni la web del dominio raíz.
- El nombre puede mostrarse completo en Kit y relativo a la zona en GoDaddy: elimina solo el sufijo DOMINIO_RAIZ si la UI lo añade automáticamente; conserva la parte news y el resto del nombre exacto. Muestra el FQDN final antes de guardar para evitar un dominio duplicado. Nunca cambies el destino/valor.
- Tras crear cada registro, dime cómo comprobarlo (dig o herramienta web) y que Matías pulse Validate en Kit; puede tardar hasta 48 h. No des por validado lo que aún no resuelve.
- No publiques un DMARC propio distinto del que Kit entrega, ni lo borres después.
- Al final, resume en 3 líneas el dominio elegido y los registros creados (sin secretos) para Matías.

Empieza verificando la elección de dominio y pidiéndome los registros que muestra Kit como texto.
---
