# Carril studio-un-autor — Javier publica sin aprobación de otra cuenta

## Decisión del operador (Matías, 2026-10-26, textual)
«Por qué restringiríamos lo que Javier puede publicar? Por qué eso de la aprobación de la otra cuenta?»
La «regla de dos personas» de Studio la introdujeron carriles de agentes (conformidad L23b); nunca fue decisión del operador. Se retira: **el autor publica solo**. Seguridad por mecanismo, no por revisión humana (doctrina FCMO: sin revisión humana obligatoria).

## Qué cambia
- Studio deja de exigir el APPROVE de otra cuenta (y el estado `reviewed` como requisito). Flujo: el autor pulsa Publicar → candidate → pushed → PR → **checks verdes** → merge → deploy → verificado. Si GitHub no permite merge sin review en el repo, Studio hace merge por la vía que hoy usa tras el review (sin crear reglas ni rulesets nuevos).
- **Se quedan intactas** todas las compuertas automáticas: publish-gate, checks de privacidad/legal/ética, diff confinado a los archivos de la pieza, verificación del deploy, reconciliación intent-before-effect, idempotencia, «el artículo cambió después de aprobarlo» (ahora: después de pulsar Publicar).
- Correo a suscriptores: NO cambia. Sigue apagado (no hay dominio; `FCMO_EMAIL_ENABLED` nunca se enciende aquí). Si `distribution.email` es true por defecto para essay/letter, déjalo en false por defecto para la primera publicación; no envíes nada.
- UI/textos: quita toda mención a «espera la aprobación de Matías/otra persona»; el botón y los mensajes dicen lo que pasa de verdad («Publicando…», «Publicado y verificado»). Español claro para Javier (no técnico).
- Opcional barato: aviso informativo (no bloqueante) en el registro/bitácora de Studio cuando algo se publica.

## Pruebas
- Las pruebas que exigían dos personas se **reescriben** para el contrato nuevo (un autor basta) — es un cambio de especificación autorizado arriba, no un debilitamiento. Cada prueba de compuerta automática se conserva sin aflojar ninguna aserción. Añade pruebas: publicar sin segunda cuenta llega a `published`; una compuerta roja sigue bloqueando; cambio tras Publicar sigue rechazado.
- En el reporte lista cada aserción eliminada o cambiada con su razón (sólo deben ser las de dos personas).

## Aceptación
- `python3 -m unittest discover -s tests -p 'test_studio_*.py'` verde (reporta conteo antes/después).
- `git diff --check` limpio.

## Prohibido
Secretos/credenciales, red, push, tocar workflows de GitHub/rulesets, encender correo, reiniciar servicios, tocar archivos fuera de `studio/` y `tests/test_studio_*.py` (salvo un NEEDS.md si hace falta, sólo añadiendo).
Commits en español con `git -c user.name=fcmo-agent -c user.email=fcmo-agent@localhost`, terminados en `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. Reporte ≤10 líneas.
