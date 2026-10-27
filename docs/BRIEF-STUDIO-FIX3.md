# Studio un autor — 3 regresiones fuera de la caja

Tu rama `studio-un-autor-20261026` pasa 280/280 dentro de la caja, pero fuera (host real, `python3 -m unittest discover -s tests -p 'test_studio_*.py'`) fallan 3 pruebas que en `origin/main` pasan (verificado: main 24/24 en esos 3 módulos). Salida completa: `docs/FALLOS-FUERA-SANDBOX.txt`.
- `test_studio_checks_privacy.PrivacyCheckTests.test_complete_invented_piece_with_company_and_quote_passes` (l.43: privacy(True)['ok'] False)
- `test_studio_integration.StudioIntegration.test_real_http_create_edit_preview_review_and_mock_publish` (l.146: algún check no ok)
- `test_studio_live.BareRemote.test_real_http_create_edit_preview_review_and_mock_publish` (l.120: POST /review/request de javier → 409)
Lee el Hub (`runtime/FCMO_RUNTIME_V1.txt`, `disciplines/SOFTWARE_ENGINEERING.md`). Encuentra la causa real (incluye por qué dentro de la caja pasaba: entorno, red, HOME, orden, archivo del host) y corrige el CÓDIGO, no las aserciones. Si una prueba describe la regla de dos personas que se quitó a propósito, cámbiala sólo para reflejar el flujo de un autor manteniendo todo lo demás que verifica, y regístralo en `studio/ASSERTION-CHANGES.md` con motivo. Agrega lo que haga que esta clase de diferencia caja/host se detecte.
Aceptación: los 3 módulos verdes y la suite `test_studio_*` completa verde; `git diff --check`. Commits en español con `git -c user.name=fcmo-agent -c user.email=fcmo-agent@localhost`, terminados en `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. Reporte ≤10 líneas.
