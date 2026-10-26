# Para Javier: pégale esto a tu Claude

Copia todo lo que está entre las líneas y pégalo en tu Claude.

---
Soy Javier y administro el DNS de fcmogroup.com. Necesito autenticar el subdominio **news.fcmogroup.com** para enviar correo de la Newsletter de FCMO AI con Kit (kit.com). Ayúdame paso a paso, una cosa a la vez y en español sencillo.

Reglas:
- No tienes que conocer los valores: Matías me los pasará desde Kit (Settings > Email > Verified Sending Domains > «Show DNS records»). **Pídeme el tipo, el host y el valor exactos de cada registro tal como los muestra Kit** (suelen ser CNAME de DKIM y un TXT de DMARC) y no inventes ninguno.
- No me pidas ni pegues contraseñas, claves de API ni códigos de acceso. Si hace falta entrar a mi proveedor de DNS, dime qué botón pulsar y yo lo hago.
- Antes de crear algo, dime si ya existe un registro con el mismo nombre en news.fcmogroup.com y no toques los registros del dominio principal (correo normal, web). Solo se agregan registros nuevos del subdominio.
- Si mi proveedor rechaza puntos en el host, usa el nombre corto (sin `.fcmogroup.com` al final; ejemplos de Kit: `cka._domainkey`).
- Tras crear cada registro, dime cómo comprobarlo (`dig` o una herramienta web) y dime que Matías haga clic en **Validate** en Kit; la propagación puede tardar hasta 48 h.
- No publiques un DMARC propio distinto del que Kit entrega, ni lo borres después.
- Al final, resume en 3 líneas qué registros quedaron creados (sin secretos) para pasárselo a Matías.

Empieza pidiéndome los registros que muestra Kit.
---
