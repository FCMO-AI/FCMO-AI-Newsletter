# Campaign 5 — L14 agents

Fecha: 2026-10-04 UTC. Rama: `c5/agents`, basada en `c5/v4`.

## Resultado

Se completó la higiene de las superficies para agentes: `llms*.txt` lleva `generated_at` y `stale_after`, organiza el contenido en las capas R0–R4, el JSON Feed dirige `external_url` a la fuente primaria, y cada Story se publica con `NewsArticle` + `isBasedOn` y un permalink de cita direccionado por SHA-256. Las versiones previas de las citas se conservan al reconstruir el candidato.

El validador nuevo corre sobre el candidato final antes de los gates de Pages. Los resultados locales pasan; el deploy y la revisión en navegador no se afirman.

## Cambios

- Actualicé los generadores de ingestión y del periódico final; las tres páginas localizadas de cada noticia comparten el mismo registro de cita inmutable.
- Añadí `tools/validate_agent_hygiene.py` para validar encabezados, jerarquía, fuentes primarias, JSON-LD, archivos de cita y retención de versiones.
- Integré el validador al workflow de Pages y a la identidad del builder para que una activación tranquila reconstruya la superficie tras cambios de código.
- Regeneré los tres artefactos derivados del generador (`release-src/feed.json`, `llms.txt`, `llms-full.txt`) y el overlay congelado. Regeneré y verifiqué el recibo de publicación.

## Evidencia

- `python3 -m unittest discover -s tests`: **563 pruebas, 0 fallas, 0 errores, 2 skips**.
- Candidato producido desde `site/data/stories.v2.json`: **459 rutas**. `validate_agent_hygiene.py`: PASS, `NewsArticle`/`isBasedOn`/citas en **41 historias × 3 idiomas**.
- `python3 tools/gates/run_all.py publish`: **13/13 PASS**, incluido `NO_FCMO_GROUP`. Hay advertencias de glosario heredadas; el gate no las convierte en fallas.
- `python3 tools/verify_release.py`: **6/6 PASS**; recibo `READY_TO_PUBLISH.md` comprobado.
- `python3 tests/oraculos/verificar_generador_newsroom.py`: PASS, incluida idempotencia y crecimiento sobre el fixture.
- La prueba de reconstrucción cambia una historia y confirma que el permalink SHA-256 anterior sigue presente junto al nuevo.
- `git diff --check`: PASS.

## Límite

No se desplegó ni se consultó el origen público. Esta caja no verificó rendering de navegador ni frescura real en producción. El chequeo de páginas comprueba JSON y las obligaciones Schema.org requeridas por este carril; no es una aprobación visual ni una señal de producción. Claude debe repetir las comprobaciones del host antes de integrar. No hubo push.

Resumen: L14 deja las superficies para agentes frescas, con jerarquía explícita y fuentes versionadas; la suite, los 13 gates y el recibo pasan localmente. Falta comprobar la publicación real y el navegador fuera de esta caja.
