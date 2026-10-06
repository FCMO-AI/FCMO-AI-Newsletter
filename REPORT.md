# L27 round 3 — FCMO AI Newsletter naming

Renamed the email product across localized signup copy, email subjects and headers, sender configuration, opt-in, privacy notices, community copy, workflow display names, and documentation. Existing web routes and `fcmo-diario` idempotency markers remain unchanged. Added a regression test for the forbidden old name and canonical EN/ES/ZH subject/header branding.

Generated HTML and plain-text previews for 2026-10-06 in English, es-419, and zh-Hans from the current public story snapshot. The 2026-10-05 captured Listmonk previews retain their dated content with the corrected product label. Their old screenshots remain historical: Playwright/Chromium is unavailable here, so no 2026-10-06 screenshots or browser proof were produced.

## Verification

- Red-first brand regression failed on the old strings before the rename; it now passes.
- `python3 -m unittest discover -s tests`: **661 tests passed, 3 skipped**.
- Kit publication candidate: **13/13 gates**; agent hygiene passed.
- Brevo publication candidate: **13/13 gates**; agent hygiene passed.
- `python3 tools/verify_release.py`: **7/7 gates passed** after rebuilding `READY_TO_PUBLISH.md` for the updated candidate.
- JSON validation and `git diff --check` passed. No provider account, production service, or reader was contacted.

The local implementation is committed on `c5/email-kit`; nothing was pushed. Production delivery and fresh browser rendering remain outside this verification.

## Resumen en español

El correo, el remitente y la suscripción ahora se llaman **FCMO AI Newsletter** en inglés, español y chino simplificado. La suite completa y las compuertas de Kit, Brevo y release pasan. Se generaron HTML y texto para hoy; las capturas actuales siguen siendo históricas porque este entorno no dispone de navegador. No se envió correo ni se hizo push.
