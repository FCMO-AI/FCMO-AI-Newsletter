# Carril studio-inventos — Studio no se queda detenido ni repite avisos (2026-10-26)

Una auditoría de reglas inventadas por agentes encontró dos en Studio. Lee el Agent Hub (`/srv/fcmo/agents/repos/FCMO-Agent-Hub/runtime/FCMO_RUNTIME_V1.txt`, si está montado) y el `AGENTS.md` de este repo.

Órdenes humanas que valen (textuales):
- Nada debe quedar «quieto o muerto, medio hecho, ignorado o fallando silenciosamente».
- A los humanos sólo les toca «la dirección».
- Intervención humana «precisa y esporádica».
- No enviar errores a Telegram; «a lo mucho un reporte ocasional de performance».

## Arreglos
1. **`studio/server/publishing.py:500,535` (commit 76dd5e0d5).** Al cuarto fallo técnico la publicación queda `halted` y sólo un humano la reanuda. Arreglo:
   - Un fallo recuperable (red, 5xx, tiempo de espera, CI ocupado) se reintenta con espera creciente y tope; la racha se reinicia al primer éxito.
   - Tras el tope, el estado pasa a `escalado`, con causa y siguiente reintento visibles en Studio, y se sigue intentando cada hora.
   - Sólo se detiene sin reintento lo que necesita a una persona: aprobación de contenido, credencial inválida, dinero, compuerta roja de contenido. La compuerta roja, el bloqueo por cambios posteriores y la regla de un solo autor no se tocan.
2. **`studio/host-ops/notify.py:125,133` (commit d3bb7911b).** Hoy avisa de inmediato cualquier estado `unknown` y repite el aviso de atasco a las dos horas. Arreglo:
   - `unknown` sólo avisa si persiste más de 30 min.
   - Un mismo problema avisa una vez, con su huella, hasta que cambie o se resuelva, y entonces avisa que se resolvió.
   - Nada de esto va a Telegram. Si hoy algo sale a Telegram, pásalo al canal de incidentes o al resumen.

## Aceptación
- `python3 -m unittest discover -s tests -p 'test_studio_*.py'` en verde, con el conteo antes y después. Ninguna aserción se debilita; si una choca, repórtala.
- Pruebas nuevas con reloj sustituido. Se ponen rojas si vuelve `halted` en el cuarto fallo recuperable, o si se repite un aviso con la misma huella.
- `docs/lanes/STUDIO-INVENTOS-HECHO.md` con el antes y el después.

## Prohibido
Secretos, red, encender el correo (`distribution.email` sigue en false), tocar otros archivos que no sean estos y sus pruebas, versionar rutas absolutas del host en reportes. Commits en `fix/studio-inventos-20261026` con `git -c user.name=fcmo-agent -c user.email=fcmo-agent@localhost`, en español, terminados en `Co-Authored-By: GPT-6 Luna <noreply@openai.com>`.

## Reporte (≤8 líneas)
